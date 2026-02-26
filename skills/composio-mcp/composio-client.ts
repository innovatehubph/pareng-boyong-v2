/**
 * Composio MCP Client - TypeScript Wrapper
 * 
 * A comprehensive TypeScript client for Composio MCP integration.
 * Provides session management, tool execution, and MCP endpoint helpers.
 * 
 * @module composio-client
 * @version 1.0.0
 */

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Supported AI provider types for Composio integration
 */
export type ProviderType = 
  | 'openai-agents'
  | 'vercel-ai'
  | 'langchain'
  | 'claude'
  | 'llamaindex'
  | 'crewai'
  | 'mcp';

/**
 * Authentication configuration for a toolkit
 */
export interface AuthConfig {
  /** Custom auth config ID (e.g., "ac_custom_config") */
  configId?: string;
  /** OAuth access token */
  accessToken?: string;
  /** API key for the service */
  apiKey?: string;
  /** Additional auth parameters */
  params?: Record<string, string>;
}

/**
 * Configuration for creating a Composio session
 */
export interface SessionConfig {
  /** List of toolkits to enable (e.g., ["github", "gmail"]) */
  toolkits?: string[];
  /** Authentication configurations per toolkit */
  authConfigs?: Record<string, string | AuthConfig>;
  /** Specific actions to include */
  actions?: string[];
  /** Entity ID for multi-tenant scenarios */
  entityId?: string;
  /** Custom metadata for the session */
  metadata?: Record<string, unknown>;
}

/**
 * MCP (Model Context Protocol) endpoint configuration
 */
export interface MCPEndpoint {
  /** The MCP server URL */
  url: string;
  /** Required headers for authentication */
  headers: Record<string, string>;
  /** WebSocket URL for streaming (if available) */
  wsUrl?: string;
}

/**
 * Composio tool definition
 */
export interface ComposioTool {
  /** Unique tool identifier */
  name: string;
  /** Human-readable description */
  description: string;
  /** JSON schema for tool parameters */
  parameters: {
    type: 'object';
    properties: Record<string, ToolParameter>;
    required?: string[];
  };
  /** The toolkit this tool belongs to */
  toolkit: string;
}

/**
 * Tool parameter definition
 */
export interface ToolParameter {
  type: string;
  description?: string;
  enum?: string[];
  default?: unknown;
  items?: ToolParameter;
}

/**
 * Result from tool execution
 */
export interface ToolExecutionResult {
  /** Whether the execution was successful */
  success: boolean;
  /** The output data from the tool */
  data?: unknown;
  /** Error message if execution failed */
  error?: string;
  /** Execution metadata */
  metadata?: {
    duration: number;
    toolName: string;
    timestamp: string;
  };
}

/**
 * Session state and information
 */
export interface SessionInfo {
  /** Session identifier */
  sessionId: string;
  /** User/entity identifier */
  userId: string;
  /** Active toolkits */
  toolkits: string[];
  /** Session creation timestamp */
  createdAt: Date;
  /** Session expiration timestamp */
  expiresAt?: Date;
  /** Current session status */
  status: 'active' | 'expired' | 'revoked';
}

/**
 * Provider interface that all AI providers must implement
 */
export interface ComposioProvider {
  /** Provider name */
  name: ProviderType;
  /** Convert Composio tools to provider-specific format */
  convertTools(tools: ComposioTool[]): unknown[];
  /** Execute a tool call */
  executeTool?(toolName: string, args: unknown): Promise<unknown>;
}

// ============================================================================
// Error Classes
// ============================================================================

/**
 * Base error class for Composio-related errors
 */
export class ComposioError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly details?: unknown
  ) {
    super(message);
    this.name = 'ComposioError';
  }
}

/**
 * Error thrown when authentication fails
 */
export class AuthenticationError extends ComposioError {
  constructor(message: string, details?: unknown) {
    super(message, 'AUTH_ERROR', details);
    this.name = 'AuthenticationError';
  }
}

/**
 * Error thrown when a session operation fails
 */
export class SessionError extends ComposioError {
  constructor(message: string, details?: unknown) {
    super(message, 'SESSION_ERROR', details);
    this.name = 'SessionError';
  }
}

/**
 * Error thrown when tool execution fails
 */
export class ToolExecutionError extends ComposioError {
  constructor(message: string, public readonly toolName: string, details?: unknown) {
    super(message, 'TOOL_EXECUTION_ERROR', details);
    this.name = 'ToolExecutionError';
  }
}

// ============================================================================
// Composio Session Class
// ============================================================================

/**
 * Represents an active Composio session with tools and MCP access
 */
export class ComposioSession {
  private _tools: ComposioTool[] | null = null;
  private _mcp: MCPEndpoint | null = null;

  constructor(
    private readonly client: ComposioClient,
    public readonly sessionInfo: SessionInfo,
    private readonly config: SessionConfig
  ) {}

  /**
   * Get the session ID
   */
  get sessionId(): string {
    return this.sessionInfo.sessionId;
  }

  /**
   * Get the user ID associated with this session
   */
  get userId(): string {
    return this.sessionInfo.userId;
  }

  /**
   * Get MCP endpoint configuration for this session
   * 
   * @returns MCP endpoint with URL and headers
   * @example
   * ```typescript
   * const { mcp } = session;
   * // Use with MCP client
   * const client = new MCPClient(mcp.url, { headers: mcp.headers });
   * ```
   */
  get mcp(): MCPEndpoint {
    if (!this._mcp) {
      this._mcp = this.client.getMCPEndpoint(this.sessionId);
    }
    return this._mcp;
  }

  /**
   * Get available tools for this session
   * 
   * @returns Promise resolving to array of Composio tools
   * @example
   * ```typescript
   * const tools = await session.tools();
   * console.log(`Available tools: ${tools.map(t => t.name).join(', ')}`);
   * ```
   */
  async tools(): Promise<ComposioTool[]> {
    if (!this._tools) {
      this._tools = await this.client.getSessionTools(this.sessionId);
    }
    return this._tools;
  }

  /**
   * Get tools converted to provider-specific format
   * 
   * @returns Promise resolving to provider-formatted tools
   */
  async getProviderTools(): Promise<unknown[]> {
    const tools = await this.tools();
    return this.client.convertToolsForProvider(tools);
  }

  /**
   * Execute a tool by name with given arguments
   * 
   * @param toolName - The name of the tool to execute
   * @param args - Arguments to pass to the tool
   * @returns Promise resolving to execution result
   * @example
   * ```typescript
   * const result = await session.executeTool('github_create_issue', {
   *   owner: 'myorg',
   *   repo: 'myrepo',
   *   title: 'Bug report',
   *   body: 'Description here'
   * });
   * ```
   */
  async executeTool(toolName: string, args: unknown): Promise<ToolExecutionResult> {
    return this.client.executeTool(this.sessionId, toolName, args);
  }

  /**
   * Refresh the session, extending its expiration
   * 
   * @returns Promise resolving to updated session info
   */
  async refresh(): Promise<SessionInfo> {
    const refreshed = await this.client.refreshSession(this.sessionId);
    Object.assign(this.sessionInfo, refreshed);
    return this.sessionInfo;
  }

  /**
   * Revoke this session, invalidating all tools and MCP access
   */
  async revoke(): Promise<void> {
    await this.client.revokeSession(this.sessionId);
    this.sessionInfo.status = 'revoked';
  }

  /**
   * Check if the session is still valid
   */
  isValid(): boolean {
    if (this.sessionInfo.status !== 'active') return false;
    if (this.sessionInfo.expiresAt && new Date() > this.sessionInfo.expiresAt) {
      return false;
    }
    return true;
  }
}

// ============================================================================
// Composio Client Configuration
// ============================================================================

/**
 * Configuration options for the Composio client
 */
export interface ComposioConfig {
  /** API key for Composio (defaults to COMPOSIO_API_KEY env var) */
  apiKey?: string;
  /** Base URL for the Composio API */
  baseUrl?: string;
  /** AI provider for tool conversion */
  provider?: ComposioProvider;
  /** Default session configuration */
  defaultSessionConfig?: SessionConfig;
  /** Request timeout in milliseconds */
  timeout?: number;
  /** Enable debug logging */
  debug?: boolean;
}

// ============================================================================
// Composio Client Class
// ============================================================================

/**
 * Main Composio client for session management and tool execution
 * 
 * @example
 * ```typescript
 * // With provider (for agent frameworks)
 * import { Composio } from './composio-client';
 * import { OpenAIAgentsProvider } from '@composio/openai-agents';
 * 
 * const composio = new Composio({ provider: new OpenAIAgentsProvider() });
 * const session = await composio.create('user_123');
 * const tools = await session.tools();
 * 
 * // MCP mode (no provider)
 * const composio = new Composio();
 * const session = await composio.create('user_123');
 * const { mcp } = session;
 * // Use mcp.url and mcp.headers with any MCP client
 * ```
 */
export class ComposioClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly provider?: ComposioProvider;
  private readonly timeout: number;
  private readonly debug: boolean;
  private readonly defaultConfig: SessionConfig;
  private sessions: Map<string, ComposioSession> = new Map();

  constructor(config: ComposioConfig = {}) {
    this.apiKey = config.apiKey || process.env.COMPOSIO_API_KEY || '';
    this.baseUrl = config.baseUrl || 'https://api.composio.dev/v1';
    this.provider = config.provider;
    this.timeout = config.timeout || 30000;
    this.debug = config.debug || false;
    this.defaultConfig = config.defaultSessionConfig || {};

    if (!this.apiKey) {
      throw new AuthenticationError(
        'Composio API key is required. Set COMPOSIO_API_KEY environment variable or pass apiKey in config.'
      );
    }
  }

  /**
   * Create a new Composio session for a user
   * 
   * @param userId - Unique identifier for the user
   * @param config - Optional session configuration
   * @returns Promise resolving to a ComposioSession
   * @example
   * ```typescript
   * const session = await composio.create('user_123', {
   *   toolkits: ['github', 'gmail'],
   *   authConfigs: { github: 'ac_custom_config' }
   * });
   * ```
   */
  async create(userId: string, config?: SessionConfig): Promise<ComposioSession> {
    const mergedConfig = { ...this.defaultConfig, ...config };
    
    this.log(`Creating session for user: ${userId}`);
    
    const response = await this.request<{ session: SessionInfo }>('/sessions', {
      method: 'POST',
      body: JSON.stringify({
        userId,
        toolkits: mergedConfig.toolkits,
        authConfigs: mergedConfig.authConfigs,
        actions: mergedConfig.actions,
        entityId: mergedConfig.entityId,
        metadata: mergedConfig.metadata,
      }),
    });

    const session = new ComposioSession(this, response.session, mergedConfig);
    this.sessions.set(session.sessionId, session);
    
    this.log(`Session created: ${session.sessionId}`);
    return session;
  }

  /**
   * Get an existing session by ID
   * 
   * @param sessionId - The session ID to retrieve
   * @returns The session if found and valid
   */
  async getSession(sessionId: string): Promise<ComposioSession | null> {
    // Check local cache first
    const cached = this.sessions.get(sessionId);
    if (cached && cached.isValid()) {
      return cached;
    }

    try {
      const response = await this.request<{ session: SessionInfo }>(
        `/sessions/${sessionId}`
      );
      
      const session = new ComposioSession(this, response.session, {});
      this.sessions.set(sessionId, session);
      return session;
    } catch (error) {
      if (error instanceof ComposioError && error.code === 'NOT_FOUND') {
        return null;
      }
      throw error;
    }
  }

  /**
   * Get MCP endpoint configuration for a session
   * 
   * @param sessionId - The session ID
   * @returns MCP endpoint configuration
   */
  getMCPEndpoint(sessionId: string): MCPEndpoint {
    return {
      url: `${this.baseUrl}/mcp/${sessionId}`,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'X-Session-Id': sessionId,
        'Content-Type': 'application/json',
      },
      wsUrl: `${this.baseUrl.replace('https://', 'wss://').replace('http://', 'ws://')}/mcp/${sessionId}/ws`,
    };
  }

  /**
   * Get tools available for a session
   * 
   * @param sessionId - The session ID
   * @returns Promise resolving to array of tools
   */
  async getSessionTools(sessionId: string): Promise<ComposioTool[]> {
    const response = await this.request<{ tools: ComposioTool[] }>(
      `/sessions/${sessionId}/tools`
    );
    return response.tools;
  }

  /**
   * Convert tools to provider-specific format
   * 
   * @param tools - Composio tools to convert
   * @returns Provider-formatted tools
   */
  convertToolsForProvider(tools: ComposioTool[]): unknown[] {
    if (!this.provider) {
      // Return raw tools if no provider configured
      return tools;
    }
    return this.provider.convertTools(tools);
  }

  /**
   * Execute a tool within a session
   * 
   * @param sessionId - The session ID
   * @param toolName - Name of the tool to execute
   * @param args - Arguments for the tool
   * @returns Promise resolving to execution result
   */
  async executeTool(
    sessionId: string,
    toolName: string,
    args: unknown
  ): Promise<ToolExecutionResult> {
    const startTime = Date.now();
    
    try {
      const response = await this.request<{ result: unknown }>(
        `/sessions/${sessionId}/tools/${toolName}/execute`,
        {
          method: 'POST',
          body: JSON.stringify({ args }),
        }
      );

      return {
        success: true,
        data: response.result,
        metadata: {
          duration: Date.now() - startTime,
          toolName,
          timestamp: new Date().toISOString(),
        },
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      throw new ToolExecutionError(message, toolName, error);
    }
  }

  /**
   * Refresh a session to extend its lifetime
   * 
   * @param sessionId - The session ID to refresh
   * @returns Promise resolving to updated session info
   */
  async refreshSession(sessionId: string): Promise<SessionInfo> {
    const response = await this.request<{ session: SessionInfo }>(
      `/sessions/${sessionId}/refresh`,
      { method: 'POST' }
    );
    return response.session;
  }

  /**
   * Revoke a session
   * 
   * @param sessionId - The session ID to revoke
   */
  async revokeSession(sessionId: string): Promise<void> {
    await this.request(`/sessions/${sessionId}`, { method: 'DELETE' });
    this.sessions.delete(sessionId);
  }

  /**
   * List all active sessions
   * 
   * @param options - Pagination and filter options
   * @returns Promise resolving to array of session info
   */
  async listSessions(options?: {
    limit?: number;
    offset?: number;
    userId?: string;
  }): Promise<SessionInfo[]> {
    const params = new URLSearchParams();
    if (options?.limit) params.set('limit', String(options.limit));
    if (options?.offset) params.set('offset', String(options.offset));
    if (options?.userId) params.set('userId', options.userId);

    const response = await this.request<{ sessions: SessionInfo[] }>(
      `/sessions?${params.toString()}`
    );
    return response.sessions;
  }

  /**
   * Get available toolkits
   * 
   * @returns Promise resolving to list of available toolkits
   */
  async getToolkits(): Promise<string[]> {
    const response = await this.request<{ toolkits: string[] }>('/toolkits');
    return response.toolkits;
  }

  /**
   * Make an authenticated API request
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
      signal: AbortSignal.timeout(this.timeout),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new ComposioError(
        error.message || `Request failed: ${response.status}`,
        error.code || 'API_ERROR',
        error
      );
    }

    return response.json();
  }

  /**
   * Log debug messages
   */
  private log(message: string): void {
    if (this.debug) {
      console.log(`[Composio] ${message}`);
    }
  }
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Create a Composio client with default configuration
 * 
 * @param config - Optional configuration
 * @returns Configured Composio client
 */
export function createComposio(config?: ComposioConfig): ComposioClient {
  return new ComposioClient(config);
}

/**
 * Type guard to check if an error is a ComposioError
 */
export function isComposioError(error: unknown): error is ComposioError {
  return error instanceof ComposioError;
}

/**
 * Format tool results for display
 */
export function formatToolResult(result: ToolExecutionResult): string {
  if (result.success) {
    return JSON.stringify(result.data, null, 2);
  }
  return `Error: ${result.error}`;
}

// ============================================================================
// Export Aliases
// ============================================================================

/**
 * Main export alias for the Composio client
 */
export const Composio = ComposioClient;
export default ComposioClient;
