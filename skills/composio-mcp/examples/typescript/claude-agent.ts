/**
 * Claude Agent SDK Integration
 * 
 * Demonstrates how to use Composio tools with Anthropic's Claude
 * for building powerful AI agents with tool use capabilities.
 * 
 * @example
 * ```bash
 * # Set environment variables
 * export COMPOSIO_API_KEY="your_composio_key"
 * export ANTHROPIC_API_KEY="your_anthropic_key"
 * 
 * # Run the example
 * npx ts-node claude-agent.ts
 * ```
 */

import Anthropic from '@anthropic-ai/sdk';
import { Composio, ComposioTool, ToolExecutionResult } from '../../composio-client';

// ============================================================================
// Type Definitions for Claude
// ============================================================================

/**
 * Claude tool definition format
 */
interface ClaudeTool {
  name: string;
  description: string;
  input_schema: {
    type: 'object';
    properties: Record<string, unknown>;
    required?: string[];
  };
}

/**
 * Claude message content types
 */
type ClaudeContentBlock = 
  | { type: 'text'; text: string }
  | { type: 'tool_use'; id: string; name: string; input: unknown }
  | { type: 'tool_result'; tool_use_id: string; content: string };

/**
 * Claude message format
 */
interface ClaudeMessage {
  role: 'user' | 'assistant';
  content: string | ClaudeContentBlock[];
}

// ============================================================================
// Claude Provider Implementation
// ============================================================================

/**
 * Provider that converts Composio tools to Claude format
 */
class ClaudeProvider {
  name = 'claude' as const;

  /**
   * Convert Composio tools to Claude tool format
   */
  convertTools(tools: ComposioTool[]): ClaudeTool[] {
    return tools.map(tool => ({
      name: tool.name,
      description: tool.description,
      input_schema: {
        type: 'object',
        properties: tool.parameters.properties,
        required: tool.parameters.required,
      },
    }));
  }
}

// ============================================================================
// Claude Agent Class
// ============================================================================

/**
 * Configuration for Claude Agent
 */
interface ClaudeAgentConfig {
  /** User ID for Composio session */
  userId: string;
  /** Toolkits to enable */
  toolkits: string[];
  /** Claude model to use */
  model?: string;
  /** System prompt */
  systemPrompt?: string;
  /** Maximum tokens for response */
  maxTokens?: number;
  /** Maximum tool use iterations */
  maxIterations?: number;
  /** Enable extended thinking (Claude 3.5+) */
  extendedThinking?: boolean;
}

/**
 * AI Agent powered by Claude and Composio tools
 */
class ClaudeAgent {
  private composio: Composio;
  private anthropic: Anthropic;
  private config: Required<ClaudeAgentConfig>;
  private session: Awaited<ReturnType<Composio['create']>> | null = null;
  private tools: ClaudeTool[] = [];
  private conversationHistory: ClaudeMessage[] = [];

  constructor(config: ClaudeAgentConfig) {
    // Initialize Composio with Claude provider
    this.composio = new Composio({
      provider: new ClaudeProvider(),
      debug: true,
    });

    // Initialize Anthropic client
    this.anthropic = new Anthropic();

    // Set defaults
    this.config = {
      userId: config.userId,
      toolkits: config.toolkits,
      model: config.model || 'claude-sonnet-4-20250514',
      systemPrompt: config.systemPrompt || this.getDefaultSystemPrompt(),
      maxTokens: config.maxTokens || 4096,
      maxIterations: config.maxIterations || 10,
      extendedThinking: config.extendedThinking || false,
    };
  }

  /**
   * Initialize the agent
   */
  async initialize(): Promise<void> {
    console.log('🚀 Initializing Claude Agent...');
    
    // Create Composio session
    this.session = await this.composio.create(this.config.userId, {
      toolkits: this.config.toolkits,
    });

    // Get and convert tools
    const composioTools = await this.session.tools();
    this.tools = (await this.session.getProviderTools()) as ClaudeTool[];

    console.log(`✅ Agent initialized with ${composioTools.length} tools:`);
    composioTools.slice(0, 10).forEach(tool => {
      console.log(`   - ${tool.name}`);
    });
    if (composioTools.length > 10) {
      console.log(`   ... and ${composioTools.length - 10} more`);
    }
  }

  /**
   * Run the agent with a user message
   */
  async run(userMessage: string): Promise<string> {
    if (!this.session) {
      throw new Error('Agent not initialized. Call initialize() first.');
    }

    console.log(`\n💬 User: ${userMessage}\n`);

    // Add user message to history
    this.conversationHistory.push({
      role: 'user',
      content: userMessage,
    });

    let iteration = 0;
    let finalResponse = '';

    while (iteration < this.config.maxIterations) {
      iteration++;
      console.log(`📍 Iteration ${iteration}/${this.config.maxIterations}`);

      // Call Claude
      const response = await this.anthropic.messages.create({
        model: this.config.model,
        max_tokens: this.config.maxTokens,
        system: this.config.systemPrompt,
        tools: this.tools,
        messages: this.conversationHistory,
      });

      console.log(`   Stop reason: ${response.stop_reason}`);

      // Process response content
      const assistantContent: ClaudeContentBlock[] = [];
      const toolUses: Array<{ id: string; name: string; input: unknown }> = [];

      for (const block of response.content) {
        if (block.type === 'text') {
          assistantContent.push({ type: 'text', text: block.text });
          finalResponse = block.text;
          console.log(`   📝 Text: ${block.text.slice(0, 100)}...`);
        } else if (block.type === 'tool_use') {
          assistantContent.push({
            type: 'tool_use',
            id: block.id,
            name: block.name,
            input: block.input,
          });
          toolUses.push({
            id: block.id,
            name: block.name,
            input: block.input,
          });
          console.log(`   🔧 Tool use: ${block.name}`);
        }
      }

      // Add assistant message to history
      this.conversationHistory.push({
        role: 'assistant',
        content: assistantContent,
      });

      // If no tool uses, we're done
      if (toolUses.length === 0 || response.stop_reason === 'end_turn') {
        console.log('\n✅ Agent completed');
        return finalResponse;
      }

      // Execute tools and add results
      const toolResults: ClaudeContentBlock[] = [];
      
      for (const toolUse of toolUses) {
        console.log(`\n   Executing: ${toolUse.name}`);
        console.log(`   Input: ${JSON.stringify(toolUse.input, null, 2)}`);

        try {
          const result = await this.session.executeTool(toolUse.name, toolUse.input);
          const resultStr = JSON.stringify(result.data);
          
          console.log(`   ✅ Result: ${resultStr.slice(0, 100)}...`);
          
          toolResults.push({
            type: 'tool_result',
            tool_use_id: toolUse.id,
            content: resultStr,
          });
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : 'Unknown error';
          console.log(`   ❌ Error: ${errorMsg}`);
          
          toolResults.push({
            type: 'tool_result',
            tool_use_id: toolUse.id,
            content: JSON.stringify({ error: errorMsg }),
          });
        }
      }

      // Add tool results as user message
      this.conversationHistory.push({
        role: 'user',
        content: toolResults,
      });
    }

    throw new Error('Maximum iterations reached');
  }

  /**
   * Stream a response with real-time output
   */
  async stream(userMessage: string): Promise<void> {
    if (!this.session) {
      throw new Error('Agent not initialized. Call initialize() first.');
    }

    console.log(`\n💬 User: ${userMessage}\n`);
    console.log('📤 Streaming response:\n');

    const stream = await this.anthropic.messages.stream({
      model: this.config.model,
      max_tokens: this.config.maxTokens,
      system: this.config.systemPrompt,
      tools: this.tools,
      messages: [{ role: 'user', content: userMessage }],
    });

    for await (const event of stream) {
      if (event.type === 'content_block_delta') {
        if (event.delta.type === 'text_delta') {
          process.stdout.write(event.delta.text);
        }
      }
    }
    console.log('\n');
  }

  /**
   * Clear conversation history
   */
  clearHistory(): void {
    this.conversationHistory = [];
    console.log('🧹 Conversation history cleared');
  }

  /**
   * Cleanup
   */
  async cleanup(): Promise<void> {
    if (this.session) {
      await this.session.revoke();
      console.log('🧹 Session revoked');
    }
  }

  private getDefaultSystemPrompt(): string {
    return `You are a helpful AI assistant powered by Claude with access to various tools.

Your capabilities include:
- Using tools to interact with external services
- Analyzing data and providing insights
- Helping users accomplish complex tasks

Guidelines:
- Use tools when they would be helpful to complete the task
- Explain what you're doing and why
- If a tool fails, try to explain the error and suggest alternatives
- Be concise but thorough in your responses`;
  }
}

// ============================================================================
// Extended Thinking Agent (Claude 3.5+)
// ============================================================================

/**
 * Agent with extended thinking capabilities
 * Uses Claude's extended thinking for complex reasoning tasks
 */
class ThinkingClaudeAgent extends ClaudeAgent {
  /**
   * Run with extended thinking enabled
   */
  async runWithThinking(userMessage: string): Promise<{
    thinking: string;
    response: string;
  }> {
    console.log(`\n💭 Running with extended thinking...`);
    console.log(`💬 User: ${userMessage}\n`);

    // Note: Extended thinking API may vary - this is a conceptual implementation
    // Adjust based on actual Anthropic SDK support
    const response = await this['anthropic'].messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 16000,
      thinking: {
        type: 'enabled',
        budget_tokens: 10000,
      },
      messages: [{ role: 'user', content: userMessage }],
    } as any);

    let thinking = '';
    let text = '';

    for (const block of response.content) {
      if (block.type === 'thinking') {
        thinking = (block as any).thinking;
        console.log('💭 Thinking:', thinking.slice(0, 200) + '...');
      } else if (block.type === 'text') {
        text = block.text;
      }
    }

    return { thinking, response: text };
  }
}

// ============================================================================
// Example Usage Functions
// ============================================================================

/**
 * Basic Claude agent example
 */
async function basicClaudeExample(): Promise<void> {
  console.log('\n' + '='.repeat(60));
  console.log('🤖 Basic Claude Agent Example');
  console.log('='.repeat(60));

  const agent = new ClaudeAgent({
    userId: 'user_claude_basic',
    toolkits: ['github'],
    model: 'claude-sonnet-4-20250514',
  });

  try {
    await agent.initialize();
    
    const response = await agent.run(
      'List my GitHub repositories and find the one with the most recent activity.'
    );
    
    console.log('\n🤖 Final Response:', response);
  } finally {
    await agent.cleanup();
  }
}

/**
 * Multi-turn conversation example
 */
async function conversationExample(): Promise<void> {
  console.log('\n' + '='.repeat(60));
  console.log('💬 Multi-turn Conversation Example');
  console.log('='.repeat(60));

  const agent = new ClaudeAgent({
    userId: 'user_claude_conversation',
    toolkits: ['github'],
  });

  try {
    await agent.initialize();
    
    // First turn
    let response = await agent.run('What GitHub repositories do I have?');
    console.log('\n🤖 Response 1:', response);

    // Second turn (continues conversation)
    response = await agent.run('Which one has the most stars?');
    console.log('\n🤖 Response 2:', response);

    // Third turn
    response = await agent.run('Create an issue in that repo about improving documentation.');
    console.log('\n🤖 Response 3:', response);
  } finally {
    await agent.cleanup();
  }
}

/**
 * Streaming example
 */
async function streamingExample(): Promise<void> {
  console.log('\n' + '='.repeat(60));
  console.log('🌊 Streaming Claude Example');
  console.log('='.repeat(60));

  const agent = new ClaudeAgent({
    userId: 'user_claude_stream',
    toolkits: ['github'],
  });

  try {
    await agent.initialize();
    await agent.stream(
      'Give me a detailed summary of my GitHub activity this week.'
    );
  } finally {
    await agent.cleanup();
  }
}

/**
 * Complex task with multiple tools
 */
async function complexTaskExample(): Promise<void> {
  console.log('\n' + '='.repeat(60));
  console.log('🔧 Complex Multi-Tool Task Example');
  console.log('='.repeat(60));

  const agent = new ClaudeAgent({
    userId: 'user_claude_complex',
    toolkits: ['github', 'gmail', 'slack'],
    maxIterations: 15,
    systemPrompt: `You are a productivity assistant that can coordinate across 
GitHub, Gmail, and Slack. Help users manage their development workflow efficiently.
When performing multi-step tasks, explain your plan first, then execute it.`,
  });

  try {
    await agent.initialize();
    
    const response = await agent.run(`
      I need to prepare a weekly status update:
      1. Check my GitHub for any merged PRs this week
      2. Look for any important emails about the project
      3. Draft a summary message
    `);
    
    console.log('\n🤖 Final Response:', response);
  } finally {
    await agent.cleanup();
  }
}

/**
 * Interactive CLI mode
 */
async function interactiveMode(): Promise<void> {
  const readline = await import('readline');
  
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const agent = new ClaudeAgent({
    userId: 'user_claude_interactive',
    toolkits: ['github', 'gmail'],
  });

  console.log('\n' + '='.repeat(60));
  console.log('🎮 Interactive Claude Agent');
  console.log('='.repeat(60));
  console.log('Commands: "exit" to quit, "clear" to reset conversation\n');

  await agent.initialize();

  const askQuestion = (): void => {
    rl.question('\n💬 You: ', async (input) => {
      const trimmed = input.trim().toLowerCase();
      
      if (trimmed === 'exit') {
        await agent.cleanup();
        rl.close();
        console.log('\n👋 Goodbye!');
        return;
      }

      if (trimmed === 'clear') {
        agent.clearHistory();
        askQuestion();
        return;
      }

      if (!trimmed) {
        askQuestion();
        return;
      }

      try {
        const response = await agent.run(input);
        console.log('\n🤖 Claude:', response);
      } catch (error) {
        console.error('\n❌ Error:', error instanceof Error ? error.message : error);
      }

      askQuestion();
    });
  };

  askQuestion();
}

// ============================================================================
// Main Entry Point
// ============================================================================

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const mode = args[0] || 'basic';

  console.log('🧠 Composio + Claude Agent Demo\n');

  switch (mode) {
    case 'basic':
      await basicClaudeExample();
      break;
    case 'conversation':
      await conversationExample();
      break;
    case 'stream':
      await streamingExample();
      break;
    case 'complex':
      await complexTaskExample();
      break;
    case 'interactive':
      await interactiveMode();
      break;
    default:
      console.log('Usage: npx ts-node claude-agent.ts [basic|conversation|stream|complex|interactive]');
      process.exit(1);
  }
}

main().catch(console.error);

export { ClaudeAgent, ClaudeProvider, ThinkingClaudeAgent };
