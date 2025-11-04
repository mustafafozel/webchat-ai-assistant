-- WebChat AI Assistant Database Initialization
-- PostgreSQL schema setup with optimizations

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
CREATE TYPE sender_type AS ENUM ('user', 'assistant');
CREATE TYPE intent_type AS ENUM ('faq', 'tool', 'general', 'greeting', 'goodbye');

-- ============================
-- Conversations Table
-- ============================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_info JSONB DEFAULT '{}',
    context JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================
-- Messages Table  
-- ============================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender sender_type NOT NULL,
    content TEXT NOT NULL,
    intent intent_type,
    metadata JSONB DEFAULT '{}',
    tokens_used INTEGER DEFAULT 0,
    processing_time FLOAT DEFAULT 0,
    tools_used TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT messages_content_not_empty CHECK (length(trim(content)) > 0)
);

-- ============================
-- Knowledge Base Table
-- ============================
CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    tags TEXT[] DEFAULT '{}',
    embedding_vector FLOAT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================
-- Analytics Table (Optional)
-- ============================
CREATE TABLE IF NOT EXISTS chat_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}',
    user_agent TEXT,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================
-- Indexes for Performance
-- ============================

-- Conversations indexes
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status) WHERE status = 'active';

-- Messages indexes  
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender);
CREATE INDEX IF NOT EXISTS idx_messages_intent ON messages(intent) WHERE intent IS NOT NULL;

-- Knowledge base indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_base_category ON knowledge_base(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_active ON knowledge_base(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_knowledge_base_tags ON knowledge_base USING GIN(tags);

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_chat_analytics_conversation_id ON chat_analytics(conversation_id);
CREATE INDEX IF NOT EXISTS idx_chat_analytics_event_type ON chat_analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_chat_analytics_created_at ON chat_analytics(created_at DESC);

-- ============================
-- Functions and Triggers
-- ============================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for conversations
CREATE TRIGGER update_conversations_updated_at 
    BEFORE UPDATE ON conversations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for knowledge_base
CREATE TRIGGER update_knowledge_base_updated_at 
    BEFORE UPDATE ON knowledge_base 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Update last_message_at when new message is added
CREATE OR REPLACE FUNCTION update_conversation_last_message()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations 
    SET last_message_at = NEW.created_at 
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_conversation_last_message_trigger
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_last_message();

-- ============================
-- Initial Data Seeding
-- ============================

-- Sample knowledge base entries
INSERT INTO knowledge_base (title, content, category, tags) VALUES
('İade Politikası', '14 gün içinde ürünlerinizi iade edebilirsiniz. Ürün orijinal ambalajında ve kullanılmamış durumda olmalıdır.', 'policy', ARRAY['iade', 'return', 'policy']),
('Kargo Bilgileri', 'Ortalama teslimat süresi 2-4 iş günüdür. Ücretsiz kargo 150 TL ve üzeri alışverişlerde geçerlidir.', 'shipping', ARRAY['kargo', 'teslimat', 'shipping', 'delivery']),
('Ödeme Seçenekleri', 'Kredi kartı, banka kartı ve kapıda ödeme seçenekleri mevcuttur. Taksit imkanı 2-12 ay arasındadır.', 'payment', ARRAY['ödeme', 'payment', 'kredi kartı', 'taksit']),
('Müşteri Hizmetleri', 'Hafta içi 09:00-18:00 saatleri arasında 444 0 123 numaralı telefondan bize ulaşabilirsiniz.', 'contact', ARRAY['iletişim', 'telefon', 'contact', 'support']),
('Üyelik İşlemleri', 'Ücretsiz üyelik oluşturabilir, siparişlerinizi takip edebilirsiniz. Üyelere özel indirimler ve kampanyalar vardır.', 'membership', ARRAY['üyelik', 'hesap', 'membership', 'account'])
ON CONFLICT DO NOTHING;

-- Sample conversation for testing (optional)
INSERT INTO conversations (session_id, user_info, context) VALUES
('demo-session-001', '{"browser": "demo", "platform": "web"}', '{"demo": true, "test_session": true}')
ON CONFLICT (session_id) DO NOTHING;

-- ============================
-- Views for Analytics
-- ============================

-- Conversation summary view
CREATE OR REPLACE VIEW conversation_summary AS
SELECT 
    c.id,
    c.session_id,
    c.status,
    c.created_at,
    c.updated_at,
    c.last_message_at,
    COUNT(m.id) as message_count,
    COUNT(CASE WHEN m.sender = 'user' THEN 1 END) as user_messages,
    COUNT(CASE WHEN m.sender = 'assistant' THEN 1 END) as assistant_messages,
    AVG(m.processing_time) as avg_processing_time,
    SUM(m.tokens_used) as total_tokens_used
FROM conversations c
LEFT JOIN messages m ON c.id = m.conversation_id
GROUP BY c.id, c.session_id, c.status, c.created_at, c.updated_at, c.last_message_at;

-- Daily stats view
CREATE OR REPLACE VIEW daily_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(*) as total_conversations,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_conversations
FROM conversations
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- ============================
-- Permissions and Security
-- ============================

-- Create application user (if needed)
-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'webchat_app') THEN
--         CREATE USER webchat_app WITH PASSWORD 'app_specific_password';
--     END IF;
-- END
-- $$;

-- Grant permissions
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO webchat_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO webchat_app;

-- ============================
-- Maintenance Procedures
-- ============================

-- Procedure to archive old conversations
CREATE OR REPLACE FUNCTION archive_old_conversations(days_old INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    affected_rows INTEGER;
BEGIN
    UPDATE conversations 
    SET status = 'archived' 
    WHERE status = 'active' 
    AND last_message_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_old;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    
    INSERT INTO chat_analytics (event_type, event_data) VALUES
    ('maintenance', jsonb_build_object('archived_conversations', affected_rows, 'days_old', days_old));
    
    RETURN affected_rows;
END;
$$ LANGUAGE plpgsql;

-- Procedure to clean up old analytics data
CREATE OR REPLACE FUNCTION cleanup_old_analytics(days_old INTEGER DEFAULT 180)
RETURNS INTEGER AS $$
DECLARE
    affected_rows INTEGER;
BEGIN
    DELETE FROM chat_analytics 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_old;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RETURN affected_rows;
END;
$$ LANGUAGE plpgsql;

-- ============================
-- Database Information
-- ============================

-- Log initialization
INSERT INTO chat_analytics (event_type, event_data) VALUES
('database_init', jsonb_build_object('version', '0.1.0', 'timestamp', CURRENT_TIMESTAMP))
ON CONFLICT DO NOTHING;

-- Show completion message
DO $$
BEGIN
    RAISE NOTICE 'WebChat AI Assistant database initialized successfully!';
    RAISE NOTICE 'Schema version: 0.1.0';
    RAISE NOTICE 'Tables created: conversations, messages, knowledge_base, chat_analytics';
    RAISE NOTICE 'Initial knowledge base entries: %', (SELECT COUNT(*) FROM knowledge_base);
END
$$;