/**
 * Integration tests for session API client
 */

import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import {
  createSession,
  getSession,
  listSessions,
  updateSessionSettings,
  addMessageToSession,
  clearConversationHistory,
  deleteSession,
  getSessionStats,
} from '../sessions';
import { mockSession, mockSessions, mockSessionStats } from '@/__tests__/mocks/data';
import { SessionStatus } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create MSW server
const server = setupServer();

// Setup and teardown
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Session API Integration Tests', () => {
  describe('createSession', () => {
    it('should create a new session successfully', async () => {
      server.use(
        http.post(`${API_URL}/sessions`, async () => {
          return HttpResponse.json({ session: mockSession });
        })
      );

      const result = await createSession({
        user_id: 'test-user',
        ttl_minutes: 60,
      });

      expect(result.data).toEqual(mockSession);
      expect(result.error).toBeUndefined();
    });

    it('should handle creation errors', async () => {
      server.use(
        http.post(`${API_URL}/sessions`, async () => {
          return HttpResponse.json(
            { detail: 'Failed to create session' },
            { status: 500 }
          );
        })
      );

      const result = await createSession({
        user_id: 'test-user',
        ttl_minutes: 60,
      });

      expect(result.data).toBeUndefined();
      expect(result.error).toBeDefined();
    });
  });

  describe('getSession', () => {
    it('should fetch session by ID successfully', async () => {
      server.use(
        http.get(`${API_URL}/sessions/:id`, async () => {
          return HttpResponse.json(mockSession);
        })
      );

      const result = await getSession('test-session-123');

      expect(result.data).toEqual(mockSession);
      expect(result.error).toBeUndefined();
    });

    it('should handle 404 errors', async () => {
      server.use(
        http.get(`${API_URL}/sessions/:id`, async () => {
          return HttpResponse.json(
            { detail: 'Session not found' },
            { status: 404 }
          );
        })
      );

      const result = await getSession('nonexistent-session');

      expect(result.data).toBeUndefined();
      expect(result.error).toBeDefined();
    });
  });

  describe('listSessions', () => {
    it('should list all sessions successfully', async () => {
      server.use(
        http.get(`${API_URL}/sessions`, async () => {
          return HttpResponse.json({
            sessions: mockSessions,
            total: mockSessions.length,
          });
        })
      );

      const result = await listSessions();

      expect(result.data?.sessions).toEqual(mockSessions);
      expect(result.data?.total).toBe(mockSessions.length);
      expect(result.error).toBeUndefined();
    });

    it('should filter sessions by user ID', async () => {
      server.use(
        http.get(`${API_URL}/sessions`, async ({ request }) => {
          const url = new URL(request.url);
          const userId = url.searchParams.get('user_id');

          const filtered = mockSessions.filter(s => s.user_id === userId);

          return HttpResponse.json({
            sessions: filtered,
            total: filtered.length,
          });
        })
      );

      const result = await listSessions('test-user');

      expect(result.data?.sessions.length).toBe(1);
      expect(result.data?.sessions[0].user_id).toBe('test-user');
    });

    it('should filter sessions by status', async () => {
      server.use(
        http.get(`${API_URL}/sessions`, async ({ request }) => {
          const url = new URL(request.url);
          const status = url.searchParams.get('status_filter') as SessionStatus;

          const filtered = mockSessions.filter(s => s.status === status);

          return HttpResponse.json({
            sessions: filtered,
            total: filtered.length,
          });
        })
      );

      const result = await listSessions(undefined, SessionStatus.ACTIVE);

      expect(result.data?.sessions.length).toBe(1);
      expect(result.data?.sessions[0].status).toBe(SessionStatus.ACTIVE);
    });
  });

  describe('updateSessionSettings', () => {
    it('should update session settings successfully', async () => {
      const updatedSession = {
        ...mockSession,
        settings: {
          ...mockSession.settings,
          use_reranking: true,
        },
      };

      server.use(
        http.put(`${API_URL}/sessions/:id/settings`, async () => {
          return HttpResponse.json(updatedSession);
        })
      );

      const result = await updateSessionSettings('test-session-123', {
        use_reranking: true,
      });

      expect(result.data?.settings.use_reranking).toBe(true);
      expect(result.error).toBeUndefined();
    });
  });

  describe('addMessageToSession', () => {
    it('should add message to session successfully', async () => {
      const updatedSession = {
        ...mockSession,
        conversation_history: [
          ...mockSession.conversation_history,
          {
            role: 'user' as const,
            content: 'New message',
            timestamp: '2025-12-28T10:30:00Z',
          },
        ],
      };

      server.use(
        http.post(`${API_URL}/sessions/:id/messages`, async () => {
          return HttpResponse.json(updatedSession);
        })
      );

      const result = await addMessageToSession(
        'test-session-123',
        'user',
        'New message'
      );

      expect(result.data?.conversation_history.length).toBe(3);
      expect(result.error).toBeUndefined();
    });
  });

  describe('clearConversationHistory', () => {
    it('should clear conversation history successfully', async () => {
      const clearedSession = {
        ...mockSession,
        conversation_history: [],
      };

      server.use(
        http.delete(`${API_URL}/sessions/:id/history`, async () => {
          return HttpResponse.json(clearedSession);
        })
      );

      const result = await clearConversationHistory('test-session-123');

      expect(result.data?.conversation_history.length).toBe(0);
      expect(result.error).toBeUndefined();
    });
  });

  describe('deleteSession', () => {
    it('should delete session successfully', async () => {
      server.use(
        http.delete(`${API_URL}/sessions/:id`, async () => {
          return HttpResponse.json({ success: true });
        })
      );

      const result = await deleteSession('test-session-123');

      expect(result.data).toEqual({ success: true });
      expect(result.error).toBeUndefined();
    });

    it('should handle deletion errors', async () => {
      server.use(
        http.delete(`${API_URL}/sessions/:id`, async () => {
          return HttpResponse.json(
            { detail: 'Session not found' },
            { status: 404 }
          );
        })
      );

      const result = await deleteSession('nonexistent-session');

      expect(result.data).toBeUndefined();
      expect(result.error).toBeDefined();
    });
  });

  describe('getSessionStats', () => {
    it('should fetch session stats successfully', async () => {
      server.use(
        http.get(`${API_URL}/sessions/stats`, async () => {
          return HttpResponse.json(mockSessionStats);
        })
      );

      const result = await getSessionStats();

      expect(result.data).toEqual(mockSessionStats);
      expect(result.error).toBeUndefined();
    });
  });

  describe('Network Errors', () => {
    it('should handle network errors gracefully', async () => {
      server.use(
        http.get(`${API_URL}/sessions/:id`, async () => {
          return HttpResponse.error();
        })
      );

      const result = await getSession('test-session-123');

      expect(result.data).toBeUndefined();
      expect(result.error).toBeDefined();
    });
  });

  describe('Timeout Handling', () => {
    it('should handle slow responses', async () => {
      server.use(
        http.get(`${API_URL}/sessions/:id`, async () => {
          await new Promise(resolve => setTimeout(resolve, 100));
          return HttpResponse.json(mockSession);
        })
      );

      const result = await getSession('test-session-123');

      expect(result.data).toEqual(mockSession);
      expect(result.error).toBeUndefined();
    });
  });
});
