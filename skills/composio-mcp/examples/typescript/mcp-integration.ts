/**
 * MCP Integration with Vercel AI SDK
 * 
 * Demonstrates how to use Composio's MCP (Model Context Protocol) endpoint
 * with the Vercel AI SDK for streaming AI interactions.
 * 
 * @example
 * ```bash
 * # Set environment variables
 * export COMPOSIO_API_KEY="your_composio_key"
 * export OPENAI_API_KEY="your_openai_key"
 * 
 * # Run the example
 * npx ts-node mcp-integration.ts
 * ```
 */

import { Composio, MCPEndpoint, ComposioTool } from '../../composio-client';
import { generateText, streamText, tool, CoreTool } from 'ai';
import { openai } from '@ai-sdk/openai';
import { anthropic } from '@ai-sdk/anthropic';
import { z } from 'zod';

// ============================================================================
// MCP Client Implementation
// ============================================================================

/**
 * Simple MCP client for communicating with Composio's MCP endpoint
 */
class MCPClient {
  constructor(
    private readonly endpoint: MCPEndpoint
  ) {}

  /**
   * List available tools from the MCP server
   */
  async listTools(): Promise<ComposioTool[]> {
    const response = await fetch(`${this.endpoint.url}/tools/list`, {
      method: 'POST',
      headers: this.endpoint.headers,
      body: JSON.stringify({ method: 'tools/list' }),
    });

    if (!response.ok) {
      throw new Error(`MCP request failed: ${response.status}`);
    }

    const data = await response.json();
    return data.tools;
  }

  /**
   * Execute a tool via MCP
   */
  async executeTool(name: string, args: unknown): Promise<unknown> {
    const response = await fetch(`${this.endpoint.url}/tools/call`, {
      method: 'POST',
      headers: this.endpoint.headers,
      body: JSON.stringify({
        method: 'tools/call',
        params: { name, arguments: args },
      }),
    });

    if (!response.ok) {
      throw new Error(`MCP tool execution failed: ${response.status}`);
    }

    const data = await response.json();
    return data.content;
  }
}

// ============================================================================
// Vercel AI SDK Integration
// ============================================================================

/**
 * Convert Composio tools to Vercel AI SDK tool format
 */
function convertToVercelTools(
  composioTools: ComposioTool[],
  mcpClient: MCPClient
): Record<string, CoreTool> {
  const tools: Record<string, CoreTool> = {};

  for (const composioTool of composioTools) {
    // Convert JSON Schema to Zod schema
    const zodSchema = jsonSchemaToZod(composioTool.parameters);

    tools[composioTool.name] = tool({
      description: composioTool.description,
      parameters: zodSchema,
      execute: async (args) => {
        console.log(`🔧 Executing via MCP: ${composioTool.name}`);
        const result = await mcpClient.executeTool(composioTool.name, args);
        return result;
      },
    });
  }

  return tools;
}

/**
 * Convert JSON Schema to Zod schema (simplified)
 * In production, use a library like json-schema-to-zod
 */
function jsonSchemaToZod(schema: ComposioTool['parameters']): z.ZodType {
  const shape: Record<string, z.ZodType> = {};

  for (const [key, prop] of Object.entries(schema.properties)) {
    let zodType: z.ZodType;

    switch (prop.type) {
      case 'string':
        zodType = prop.enum 
          ? z.enum(prop.enum as [string, ...string[]])
          : z.string();
        if (prop.description) {
          zodType = zodType.describe(prop.description);
        }
        break;
      case 'number':
      case 'integer':
        zodType = z.number();
        break;
      case 'boolean':
        zodType = z.boolean();
        break;
      case 'array':
        zodType = z.array(z.any());
        break;
      case 'object':
        zodType = z.record(z.any());
        break;
      default:
        zodType = z.any();
    }

    // Make optional if not required
    if (!schema.required?.includes(key)) {
      zodType = zodType.optional();
    }

    shape[key] = zodType;
  }

  return z.object(shape);
}

// ============================================================================
// Streaming Chat Implementation
// ============================================================================

/**
 * Create a streaming chat interface using Vercel AI SDK
 */
class MCPStreamingChat {
  private composio: Composio;
  private session: Awaited<ReturnType<Composio['create']>> | null = null;
  private mcpClient: MCPClient | null = null;
  private tools: Record<string, CoreTool> = {};

  constructor(
    private readonly userId: string,
    private readonly toolkits: string[]
  ) {
    this.composio = new Composio({ debug: true });
  }

  /**
   * Initialize the MCP connection
   */
  async initialize(): Promise<void> {
    console.log('🔗 Connecting to Composio MCP...');

    // Create session
    this.session = await this.composio.create(this.userId, {
      toolkits: this.toolkits,
    });

    // Get MCP endpoint
    const { mcp } = this.session;
    console.log(`📡 MCP Endpoint: ${mcp.url}`);

    // Create MCP client
    this.mcpClient = new MCPClient(mcp);

    // Fetch and convert tools
    const composioTools = await this.mcpClient.listTools();
    this.tools = convertToVercelTools(composioTools, this.mcpClient);

    console.log(`✅ Connected with ${Object.keys(this.tools).length} tools`);
  }

  /**
   * Generate a complete response (non-streaming)
   */
  async generate(
    prompt: string,
    options?: { model?: 'openai' | 'anthropic' }
  ): Promise<string> {
    const model = options?.model === 'anthropic'
      ? anthropic('claude-3-5-sonnet-20241022')
      : openai('gpt-4-turbo-preview');

    console.log(`\n💬 Prompt: ${prompt}`);
    console.log('⏳ Generating response...\n');

    const { text, toolCalls, toolResults } = await generateText({
      model,
      tools: this.tools,
      maxSteps: 5,
      prompt,
      system: `You are a helpful AI assistant with access to various tools.
Use tools when needed to help accomplish tasks. Be concise and helpful.`,
    });

    // Log tool usage
    if (toolCalls && toolCalls.length > 0) {
      console.log(`\n🔧 Tool calls made: ${toolCalls.length}`);
      toolCalls.forEach((call, i) => {
        console.log(`   ${i + 1}. ${call.toolName}`);
      });
    }

    return text;
  }

  /**
   * Stream a response with real-time output
   */
  async stream(
    prompt: string,
    options?: { model?: 'openai' | 'anthropic' }
  ): Promise<void> {
    const model = options?.model === 'anthropic'
      ? anthropic('claude-3-5-sonnet-20241022')
      : openai('gpt-4-turbo-preview');

    console.log(`\n💬 Prompt: ${prompt}`);
    console.log('📤 Streaming response:\n');

    const result = await streamText({
      model,
      tools: this.tools,
      maxSteps: 5,
      prompt,
      system: `You are a helpful AI assistant with access to various tools.
Use tools when needed to help accomplish tasks. Be concise and helpful.`,
      onStepFinish: ({ text, toolCalls, toolResults }) => {
        if (toolCalls && toolCalls.length > 0) {
          console.log('\n🔧 Tool call:');
          toolCalls.forEach(call => {
            console.log(`   - ${call.toolName}: ${JSON.stringify(call.args)}`);
          });
        }
      },
    });

    // Stream the text output
    for await (const textPart of result.textStream) {
      process.stdout.write(textPart);
    }
    console.log('\n');
  }

  /**
   * Multi-turn conversation
   */
  async chat(messages: Array<{ role: 'user' | 'assistant'; content: string }>): Promise<string> {
    const model = openai('gpt-4-turbo-preview');

    const { text } = await generateText({
      model,
      tools: this.tools,
      maxSteps: 5,
      messages: [
        { role: 'system', content: 'You are a helpful assistant with tool access.' },
        ...messages,
      ],
    });

    return text;
  }

  /**
   * Cleanup
   */
  async close(): Promise<void> {
    if (this.session) {
      await this.session.revoke();
      console.log('🔌 MCP session closed');
    }
  }
}

// ============================================================================
// Example Usage
// ============================================================================

/**
 * Basic MCP example with text generation
 */
async function basicMCPExample(): Promise<void> {
  console.log('\n' + '='.repeat(60));
  console.log('📡 Basic MCP Integration Example');
  console.log('='.repeat(60));

  const chat = new MCPStreamingChat('user_mcp_basic', ['github']);

  try {
    await chat.initialize();
    
    const response = await chat.generate(
      'List my GitHub repositories and tell me which one has the most stars.'
    );
    
    console.log('\n🤖 Response:', response);
  } finally {
    await chat.close();
  }
}

/**
 * Streaming example
 */
async function streamingExample(): Promise<void> {
  console.log('\n' + '='.repeat(60));
  console.log('🌊 Streaming MCP Example');
  console.log('='.repeat(60));

  const chat = new MCPStreamingChat('user_mcp_stream', ['github', 'gmail']);

  try {
    await chat.initialize();
    
    await chat.stream(
      'Check my GitHub notifications and summarize any important ones.'
    );
  } finally {
    await chat.close();
  }
}

/**
 * Multi-model example (switching between OpenAI and Anthropic)
 */
async function multiModelExample(): Promise<void> {
  console.log('\n' + '='.repeat(60));
  console.log('🔄 Multi-Model MCP Example');
  console.log('='.repeat(60));

  const chat = new MCPStreamingChat('user_mcp_multi', ['github']);

  try {
    await chat.initialize();
    
    console.log('\n--- Using OpenAI GPT-4 ---');
    const openaiResponse = await chat.generate(
      'What repositories do I have?',
      { model: 'openai' }
    );
    console.log('OpenAI:', openaiResponse);

    console.log('\n--- Using Anthropic Claude ---');
    const claudeResponse = await chat.generate(
      'Summarize my GitHub activity.',
      { model: 'anthropic' }
    );
    console.log('Claude:', claudeResponse);
  } finally {
    await chat.close();
  }
}

/**
 * Direct MCP client usage (without Vercel AI SDK)
 */
async function directMCPExample(): Promise<void> {
  console.log('\n' + '='.repeat(60));
  console.log('🔌 Direct MCP Client Example');
  console.log('='.repeat(60));

  const composio = new Composio();
  const session = await composio.create('user_direct_mcp', {
    toolkits: ['github'],
  });

  // Get MCP endpoint
  const { mcp } = session;
  console.log('MCP URL:', mcp.url);
  console.log('MCP Headers:', Object.keys(mcp.headers));

  // Create client and list tools
  const client = new MCPClient(mcp);
  const tools = await client.listTools();

  console.log('\nAvailable MCP Tools:');
  tools.slice(0, 5).forEach(tool => {
    console.log(`  - ${tool.name}: ${tool.description.slice(0, 50)}...`);
  });

  // Execute a tool directly
  console.log('\nExecuting github_list_repos...');
  try {
    const result = await client.executeTool('github_list_repos', {
      per_page: 5,
    });
    console.log('Result:', JSON.stringify(result, null, 2).slice(0, 200) + '...');
  } catch (error) {
    console.log('Tool execution requires authentication. Connect GitHub first.');
  }

  await session.revoke();
}

// ============================================================================
// Next.js API Route Example
// ============================================================================

/**
 * Example Next.js API route handler for MCP streaming
 * 
 * @example
 * ```typescript
 * // app/api/chat/route.ts
 * import { mcpApiHandler } from './mcp-integration';
 * export const POST = mcpApiHandler;
 * ```
 */
export async function mcpApiHandler(req: Request): Promise<Response> {
  const { messages, userId } = await req.json();

  const composio = new Composio();
  const session = await composio.create(userId || 'anonymous', {
    toolkits: ['github', 'gmail'],
  });

  const mcpClient = new MCPClient(session.mcp);
  const composioTools = await mcpClient.listTools();
  const tools = convertToVercelTools(composioTools, mcpClient);

  const result = await streamText({
    model: openai('gpt-4-turbo-preview'),
    tools,
    maxSteps: 5,
    messages,
  });

  return result.toDataStreamResponse();
}

// ============================================================================
// Main Entry Point
// ============================================================================

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const mode = args[0] || 'basic';

  console.log('🌐 Composio MCP + Vercel AI SDK Demo\n');

  switch (mode) {
    case 'basic':
      await basicMCPExample();
      break;
    case 'stream':
      await streamingExample();
      break;
    case 'multi':
      await multiModelExample();
      break;
    case 'direct':
      await directMCPExample();
      break;
    default:
      console.log('Usage: npx ts-node mcp-integration.ts [basic|stream|multi|direct]');
      process.exit(1);
  }
}

main().catch(console.error);

export { MCPClient, MCPStreamingChat, convertToVercelTools };
