-- postgres-init/01-add-embedding.sql
ALTER TABLE academic_sources
ADD COLUMN IF NOT EXISTS embedding vector(384);
-- The dimension (768) should match the dimension of the embeddings, 
--768 works with common Hugging Face embedding models like sentence-transformers/all-MiniLM-L6-v2 