import os
from pydantic import BaseModel, Field, model_validator
from typing import Literal
class Config(BaseModel):
   model: str = "gemini-3.6-flash"
   knowledge_source: Literal["local"] = "local"
   local_knowledge_directory: str = "knowledge"

   project_id: str | None = None
   location: str = "global"
   knowledge_bucket: str | None = None


   @model_validator(mode = "after")
   def validate_cloud_config(self):
        if self.knowledge_source == "cloud":
            missing = []
            if not self.project_id:
                missing.append("GOOGLE_CLOUD_PROJECT")
            if not self.knowledge_bucket:
                missing.append("KNOWLEDGE_BUCKET")
            if missing:
                raise ValidationError(f"Missing required fields: {missing}")
        return self

def load_config() -> Config:
    return Config(
        model =os.getenv("MODEL", "gemini-3.6-flash"),
        knowledge_source =os.getenv("KNOWLEDGE_SOURCE", "local"),
        local_knowledge_directory =os.getenv("LOCAL_KNOWLEDGE_DIRECTORY", "knowledge")
    )