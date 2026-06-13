"""
OralLex Unified Knowledge Publisher.

Routes generated artifacts to the correct external integration or 
internal AgentOS shared memory based on user configuration.
"""

import os
from datetime import datetime
from loguru import logger
from typing import Literal

from orallex.models.schemas import KnowledgeArtifact, PublishConfig, PublishResult
from orallex.integrations.notion import NotionPublisher
from orallex.integrations.confluence import ConfluencePublisher
# from orallex.db.chroma_client import AgentOSChromaClient # To be implemented in final hour

class KnowledgePublisher:
    """Route to correct integration based on user's configured destination."""
    
    def __init__(self):
        # In a real app, keys would be injected via settings or user oauth tokens
        self.notion_pub = NotionPublisher(api_key="mock_notion_key")
        self.conf_pub = ConfluencePublisher(api_token="mock", domain="mock", username="mock")

    async def publish(
        self,
        artifact: KnowledgeArtifact,
        destination: Literal["notion", "confluence", "markdown_file", "agentOS"],
        config: PublishConfig
    ) -> PublishResult:
        """Main routing method for publishing artifacts."""
        
        logger.info(f"Routing artifact {artifact.artifact_id} to {destination}")
        
        try:
            url = None
            
            if destination == "notion":
                url = await self.notion_pub.create_artifact_page(
                    artifact, 
                    database_id=config.notion_database_id or "", 
                    template_page_id=config.parent_page_id
                )
                
            elif destination == "confluence":
                url = await self.conf_pub.create_page(
                    artifact,
                    space_key=config.confluence_space_key or "",
                    parent_page_id=config.parent_page_id
                )
                
            elif destination == "markdown_file":
                url = await self.export_to_markdown_file(artifact)
                
            elif destination == "agentOS":
                success = await self.publish_to_agentOS(artifact, config.org_id or "default_org")
                if success:
                    url = f"agentos://knowledge/{artifact.artifact_id}"
            
            else:
                return PublishResult(success=False, error_message=f"Unknown destination: {destination}")

            return PublishResult(
                success=True,
                url=url,
                published_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Publishing to {destination} failed: {e}")
            return PublishResult(success=False, error_message=str(e))

    async def publish_to_agentOS(self, artifact: KnowledgeArtifact, org_id: str) -> bool:
        """
        Store in ChromaDB for semantic search by other AgentOS agents.
        Write metadata to PostgreSQL.
        Update agentOS:memory:knowledge:{org_id} in Redis.
        """
        logger.info(f"Publishing to AgentOS shared memory for org: {org_id}")
        
        # 1. Store in ChromaDB (Mock)
        # chroma_client.add(documents=[artifact.markdown_content], metadatas=[{"id": artifact.artifact_id}])
        
        # 2. Write Metadata to Postgres (Mock)
        
        # 3. Update Redis cache (Mock)
        
        return True

    async def export_to_markdown_file(self, artifact: KnowledgeArtifact) -> str:
        """
        For users without Notion/Confluence:
        Generate clean Markdown file with YAML frontmatter.
        """
        # Create safe filename
        safe_topic = artifact.title.lower().replace(" ", "_").replace("/", "-")
        date_str = datetime.utcnow().strftime("%Y%m%d")
        filename = f"{artifact.artifact_type}_{safe_topic}_{date_str}.md"
        
        # Add YAML Frontmatter
        frontmatter = f"---\nauthor: OralLex Socratic Capture\ndate: {date_str}\ntopic: {artifact.title}\nsession_id: {artifact.session_id}\ntype: {artifact.artifact_type}\n---\n\n"
        
        full_content = frontmatter + artifact.markdown_content
        
        # Ensure export directory exists
        export_dir = "downloads"
        os.makedirs(export_dir, exist_ok=True)
        
        filepath = os.path.join(export_dir, filename)
        
        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_content)
            
        logger.info(f"Exported markdown file to {filepath}")
        return filepath
