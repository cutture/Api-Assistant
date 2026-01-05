/**
 * Mock data for testing
 */

import { Session, SessionStatus, DiagramResponse, DiagramType } from '@/types';

export const mockSession: Session = {
  session_id: 'test-session-123',
  user_id: 'test-user',
  created_at: '2025-12-28T10:00:00Z',
  last_accessed: '2025-12-28T10:30:00Z',
  expires_at: '2025-12-28T11:00:00Z',
  status: SessionStatus.ACTIVE,
  settings: {
    default_search_mode: 'hybrid',
    default_n_results: 10,
    use_reranking: true,
    use_query_expansion: false,
    use_diversification: false,
    show_scores: true,
    show_metadata: true,
    max_content_length: 500,
    custom_metadata: {},
  },
  conversation_history: [
    {
      role: 'user',
      content: 'How do I authenticate?',
      timestamp: '2025-12-28T10:10:00Z',
    },
    {
      role: 'assistant',
      content: 'You can authenticate using Bearer tokens...',
      timestamp: '2025-12-28T10:10:05Z',
    },
  ],
  metadata: {},
  collection_name: 'test-collection',
};

export const mockSessions: Session[] = [
  mockSession,
  {
    ...mockSession,
    session_id: 'test-session-456',
    status: SessionStatus.INACTIVE,
    user_id: undefined,
  },
  {
    ...mockSession,
    session_id: 'test-session-789',
    status: SessionStatus.EXPIRED,
    conversation_history: [],
  },
];

export const mockSessionStats = {
  total_sessions: 10,
  active_sessions: 5,
  inactive_sessions: 3,
  expired_sessions: 2,
};

export const mockDiagramResponse: DiagramResponse = {
  diagram_type: DiagramType.SEQUENCE,
  mermaid_code: `sequenceDiagram
    participant Client
    participant API
    participant Backend
    Client->>API: GET /api/users
    API->>Backend: Query users
    Backend-->>API: Return data
    API-->>Client: 200 OK`,
  title: 'User API Sequence',
};

export const mockAuthFlowDiagram: DiagramResponse = {
  diagram_type: DiagramType.FLOWCHART,
  mermaid_code: `flowchart TD
    A[Start] --> B{Authenticated?}
    B -->|Yes| C[Access Resource]
    B -->|No| D[Request Token]
    D --> E[Validate Credentials]
    E -->|Valid| F[Issue Token]
    E -->|Invalid| G[Deny Access]
    F --> C
    G --> H[End]
    C --> H`,
  title: 'Bearer Authentication Flow',
};
