/**
 * Basic Agent Example with OpenAI Agents SDK
 * 
 * Demonstrates how to use Composio tools with the OpenAI Agents SDK
 * to create an AI agent that can interact with external services.
 * 
 * @example
 * ```bash
 * # Set environment variables
 * export COMPOSIO_API_KEY="your_composio_key"
 * export OPENAI_API_KEY="your_openai_key"
 * 
 * # Run the example
 * npx ts-node basic-agent.ts
 * ```
 */

import { Composio, ComposioTool, ToolExecutionResult } from '../../composio-client';
import OpenAI from 'openai';

// ============================================================================
// OpenAI Agents Provider Implementation
// ============================================================================

/**
 * Provider that converts Composio tools to OpenAI function format
 */
class OpenAIAgentsProvider {
  name = 'openai-agents' as const;

  /**
   * Convert Composio tools to OpenAI function calling format
   */
  convertTools(tools: ComposioTool[]): OpenAI.Chat.Completions.ChatCompletionTool[] {
    return tools.map(tool => ({
      type: 'function' as const,
      function: {
        name: tool.name,
        description: tool.description,
        parameters: tool.parameters,
      },
    }));
  }
}

// ============================================================================
// Agent Configuration
// ============================================================================

interface AgentConfig {
  /** User ID for the Composio session */
  userId: string;
  /** Toolkits to enable */
  toolkits: string[];
  /** OpenAI model to use */
  model?: string;
  /** System prompt for the agent */
  systemPrompt?: string;
  /** Maximum iterations for tool calls */
  maxIterations?: number;
}

// ============================================================================
// Composio Agent Class
// ============================================================================

/**
 * AI Agent powered by OpenAI and Composio tools
 */
class ComposioAgent {
  private composio: Composio;
  private openai: OpenAI;
  private config: Required<AgentConfig>;
  private session: Awaited<ReturnType<Composio['create']>> | null = null;
  private tools: OpenAI.Chat.Completions.ChatCompletionTool[] = [];

  constructor(config: AgentConfig) {
    // Initialize Composio with OpenAI provider
    this.composio = new Composio({
      provider: new OpenAIAgentsProvider(),
      debug: true,
    });

    // Initialize OpenAI client
    this.openai = new OpenAI();

    // Set defaults
    this.config = {
      userId: config.userId,
      toolkits: config.toolkits,
      model: config.model || 'gpt-4-turbo-preview',
      systemPrompt: config.systemPrompt || this.getDefaultSystemPrompt(),
      maxIterations: config.maxIterations || 10,
    };
  }

  /**
   * Initialize the agent by creating a Composio session
   */
  async initialize(): Promise<void> {
    console.log('🚀 Initializing Composio Agent...');
    
    // Create session with specified toolkits
    this.session = await this.composio.create(this.config.userId, {
      toolkits: this.config.toolkits,
    });

    // Get and convert tools
    const composioTools = await this.session.tools();
    this.tools = await this.session.getProviderTools() as OpenAI.Chat.Completions.ChatCompletionTool[];

    console.log(`✅ Agent initialized with ${composioTools.length} tools:`);
    composioTools.forEach(tool => {
      console.log(`   - ${tool.name}: ${tool.description.slice(0, 60)}...`);
    });
  }

  /**
   * Run the agent with a user message
   */
  async run(userMessage: string): Promise<string> {
    if (!this.session) {
      throw new Error('Agent not initialized. Call initialize() first.');
    }

    console.log(`\n💬 User: ${userMessage}\n`);

    const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [
      { role: 'system', content: this.config.systemPrompt },
      { role: 'user', content: userMessage },
    ];

    let iteration = 0;
    
    while (iteration < this.config.maxIterations) {
      iteration++;
      console.log(`📍 Iteration ${iteration}/${this.config.maxIterations}`);

      // Call OpenAI
      const response = await this.openai.chat.completions.create({
        model: this.config.model,
        messages,
        tools: this.tools.length > 0 ? this.tools : undefined,
        tool_choice: this.tools.length > 0 ? 'auto' : undefined,
      });

      const assistantMessage = response.choices[0].message;
      messages.push(assistantMessage);

      // Check if we're done (no tool calls)
      if (!assistantMessage.tool_calls || assistantMessage.tool_calls.length === 0) {
        console.log('\n✅ Agent completed');
        return assistantMessage.content || 'No response generated.';
      }

      // Execute tool calls
      for (const toolCall of assistantMessage.tool_calls) {
        const toolName = toolCall.function.name;
        const toolArgs = JSON.parse(toolCall.function.arguments);

        console.log(`🔧 Executing tool: ${toolName}`);
        console.log(`   Args: ${JSON.stringify(toolArgs, null, 2)}`);

        try {
          const result = await this.session.executeTool(toolName, toolArgs);
          
          console.log(`   ✅ Success: ${JSON.stringify(result.data).slice(0, 100)}...`);

          messages.push({
            role: 'tool',
            tool_call_id: toolCall.id,
            content: JSON.stringify(result.data),
          });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          console.log(`   ❌ Error: ${errorMessage}`);

          messages.push({
            role: 'tool',
            tool_call_id: toolCall.id,
            content: JSON.stringify({ error: errorMessage }),
          });
        }
      }
    }

    throw new Error('Maximum iterations reached without completion');
  }

  /**
   * Clean up the agent session
   */
  async cleanup(): Promise<void> {
    if (this.session) {
      await this.session.revoke();
      console.log('🧹 Session revoked');
    }
  }

  private getDefaultSystemPrompt(): string {
    return `You are a helpful AI assistant with access to various tools.
Use the available tools to help the user accomplish their tasks.
Always explain what you're doing and provide clear, helpful responses.
If a tool call fails, try to explain the error and suggest alternatives.`;
  }
}

// ============================================================================
// Example Usage Functions
// ============================================================================

/**
 * Example: GitHub Repository Manager
 */
async function githubExample(): Promise<void> {
  console.log('\n' + '='.repeat(60));
  console.log('📦 GitHub Repository Manager Example');
  console.log('='.repeat(60));

  const agent = new ComposioAgent({
    userId: 'user_github_demo',
    toolkits: ['github'],
    systemPrompt: `You are a GitHub assistant. Help users manage their repositories,
issues, pull requests, and other GitHub-related tasks.`,
  });

  try {
    await agent.initialize();
    
    const response = await agent.run(
      'List my recent GitHub repositories and summarize their activity.'
    );
    
    console.log('\n🤖 Assistant:', response);
  } finally {
    await agent.cleanup();
  }
}

/**
 * Example: Gmail Email Assistant
 */
async function gmailExample(): Promise<void> {
  console.log('\n' + '='.repeat(60));
  console.log('📧 Gmail Email Assistant Example');
  console.log('='.repeat(60));

  const agent = new ComposioAgent({
    userId: 'user_gmail_demo',
    toolkits: ['gmail'],
    systemPrompt: `You are an email assistant. Help users read, compose, and manage
their Gmail messages efficiently.`,
  });

  try {
    await agent.initialize();
    
    const response = await agent.run(
      'Check my inbox for any unread messages from today and summarize them.'
    );
    
    console.log('\n🤖 Assistant:', response);
  } finally {
    await agent.cleanup();
  }
}

/**
 * Example: Multi-toolkit Agent
 */
async function multiToolkitExample(): Promise<void> {
  console.log('\n' + '='.repeat(60));
  console.log('🔧 Multi-Toolkit Agent Example');
  console.log('='.repeat(60));

  const agent = new ComposioAgent({
    userId: 'user_multi_demo',
    toolkits: ['github', 'gmail', 'slack', 'notion'],
    model: 'gpt-4-turbo-preview',
    systemPrompt: `You are a productivity assistant with access to multiple tools.
You can help users manage their GitHub repositories, emails, Slack messages,
and Notion documents. Coordinate across tools when needed.`,
    maxIterations: 15,
  });

  try {
    await agent.initialize();
    
    const response = await agent.run(
      'Create a GitHub issue about implementing a new feature, ' +
      'then send a Slack message to the team about it.'
    );
    
    console.log('\n🤖 Assistant:', response);
  } finally {
    await agent.cleanup();
  }
}

// ============================================================================
// Interactive Mode
// ============================================================================

/**
 * Run agent in interactive mode
 */
async function interactiveMode(): Promise<void> {
  const readline = await import('readline');
  
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const agent = new ComposioAgent({
    userId: 'user_interactive',
    toolkits: ['github', 'gmail'],
  });

  console.log('\n' + '='.repeat(60));
  console.log('🎮 Interactive Mode');
  console.log('='.repeat(60));
  console.log('Type your messages and press Enter. Type "exit" to quit.\n');

  await agent.initialize();

  const askQuestion = (): void => {
    rl.question('\n💬 You: ', async (input) => {
      const trimmed = input.trim();
      
      if (trimmed.toLowerCase() === 'exit') {
        await agent.cleanup();
        rl.close();
        console.log('\n👋 Goodbye!');
        return;
      }

      if (!trimmed) {
        askQuestion();
        return;
      }

      try {
        const response = await agent.run(trimmed);
        console.log('\n🤖 Assistant:', response);
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
  const mode = args[0] || 'github';

  console.log('🤖 Composio + OpenAI Agents Demo\n');

  switch (mode) {
    case 'github':
      await githubExample();
      break;
    case 'gmail':
      await gmailExample();
      break;
    case 'multi':
      await multiToolkitExample();
      break;
    case 'interactive':
      await interactiveMode();
      break;
    default:
      console.log('Usage: npx ts-node basic-agent.ts [github|gmail|multi|interactive]');
      process.exit(1);
  }
}

// Run if executed directly
main().catch(console.error);

export { ComposioAgent, OpenAIAgentsProvider };
