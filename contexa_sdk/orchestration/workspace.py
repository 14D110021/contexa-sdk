"""
Shared workspace and artifact system for agent collaboration.

This module provides workspace structures for agents to share and collaborate
on persistent artifacts like documents, code, and datasets.
"""

import time
import uuid
from typing import Dict, Any, List, Optional, Union

class Artifact:
    """Versioned content artifact in a shared workspace.
    
    Artifacts represent persistent objects that agents can create and modify,
    with tracking of all changes and history.
    
    Attributes:
        name (str): Name of the artifact
        content (Any): Current content of the artifact
        artifact_type (str): Type of artifact (document, code, data, etc.)
        creator_id (str): ID of the agent that created the artifact
        artifact_id (str): Unique identifier for the artifact
        version (int): Current version number
        version_history (List[Dict]): Previous versions of the artifact
        metadata (Dict): Additional information about the artifact
        
    Example:
        ```python
        # Create an artifact
        document = Artifact(
            name="Research Report",
            content={"title": "Quantum Computing Research", "sections": [...]},
            artifact_type="document",
            creator_id="research_agent",
            metadata={"priority": "high", "status": "draft"}
        )
        
        # Update the artifact
        document.update(
            new_content={"title": "Quantum Computing Research", "sections": [...], "appendix": [...]},
            editor_id="editing_agent",
            comment="Added appendix section"
        )
        ```
    """
    
    def __init__(
        self,
        name: str,
        content: Any,
        artifact_type: str = "generic",
        creator_id: str = None,
        artifact_id: str = None,
        metadata: Dict[str, Any] = None
    ):
        self.name = name
        self.content = content
        self.artifact_type = artifact_type
        self.creator_id = creator_id
        self.artifact_id = artifact_id or str(uuid.uuid4())
        self.version = 1
        self.created_at = time.time()
        self.updated_at = self.created_at
        self.metadata = metadata or {}
        
        # Version history stores previous versions
        self.version_history = []
        
    def update(
        self,
        new_content: Any,
        editor_id: str,
        comment: str = "",
        metadata_updates: Dict[str, Any] = None
    ) -> int:
        """Update the artifact with new content
        
        Args:
            new_content: The new content for the artifact
            editor_id: ID of the agent making the update
            comment: Optional comment about the changes
            metadata_updates: Optional updates to metadata
            
        Returns:
            New version number
        """
        # Archive the current version before updating
        self.version_history.append({
            "version": self.version,
            "content": self.content,
            "updated_at": self.updated_at,
            "editor_id": self.creator_id if self.version == 1 else None,
            "metadata": self.metadata.copy()
        })
        
        # Update to new version
        self.version += 1
        self.content = new_content
        self.updated_at = time.time()
        
        # Update metadata if provided
        if metadata_updates:
            self.metadata.update(metadata_updates)
            
        return self.version
        
    def get_version(self, version_number: int) -> Dict[str, Any]:
        """Get a specific version of the artifact
        
        Args:
            version_number: The version number to retrieve
            
        Returns:
            The artifact version data
            
        Raises:
            ValueError: If the version does not exist
        """
        if version_number == self.version:
            # Return current version
            return {
                "version": self.version,
                "content": self.content,
                "updated_at": self.updated_at,
                "metadata": self.metadata
            }
        
        # Look in history for older versions
        for version in self.version_history:
            if version["version"] == version_number:
                return version
                
        raise ValueError(f"Version {version_number} does not exist")
        
    def get_history(self) -> List[Dict[str, Any]]:
        """Get the complete version history of the artifact
        
        Returns:
            List of all versions from oldest to newest
        """
        # Return history plus current version
        history = self.version_history.copy()
        history.append({
            "version": self.version,
            "content": self.content,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        })
        
        return history
        
    def to_dict(self) -> Dict[str, Any]:
        """Get the artifact as a dictionary
        
        Returns:
            Dictionary representation of the artifact
        """
        return {
            "artifact_id": self.artifact_id,
            "name": self.name,
            "content": self.content,
            "artifact_type": self.artifact_type,
            "creator_id": self.creator_id,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }


class SharedWorkspace:
    """Collaborative workspace for artifacts shared between agents.
    
    A SharedWorkspace represents a persistent environment where agents can
    share and collaborate on artifacts, with tracking of all changes.
    
    Attributes:
        name (str): Name of the workspace
        artifacts (Dict[str, Artifact]): Artifacts in the workspace
        activities (List[Dict]): Log of all activities in the workspace
        workspace_id (str): Unique identifier for the workspace
        metadata (Dict): Additional information about the workspace
        
    Example:
        ```python
        # Create a workspace
        workspace = SharedWorkspace(name="Research Project Workspace")
        
        # Add an artifact
        doc_id = workspace.add_artifact(
            name="Research Report",
            content={"title": "Initial Draft", "content": "..."},
            creator_id="research_agent"
        )
        
        # Update the artifact
        workspace.update_artifact(
            artifact_id=doc_id,
            content={"title": "Revised Draft", "content": "..."},
            editor_id="editing_agent",
            comment="Improved clarity and fixed issues"
        )
        
        # Get the artifact
        document = workspace.get_artifact(doc_id)
        
        # Get artifact history
        history = workspace.get_artifact_history(doc_id)
        ```
    """
    
    def __init__(
        self,
        name: str = "Default Workspace",
        workspace_id: str = None,
        metadata: Dict[str, Any] = None
    ):
        self.name = name
        self.artifacts: Dict[str, Artifact] = {}
        self.activities: List[Dict[str, Any]] = []
        self.workspace_id = workspace_id or str(uuid.uuid4())
        self.created_at = time.time()
        self.metadata = metadata or {}
        
    def add_artifact(
        self,
        name: str,
        content: Any,
        creator_id: str,
        artifact_type: str = "generic",
        artifact_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add a new artifact to the workspace
        
        Args:
            name: Name of the artifact
            content: Content of the artifact
            creator_id: ID of the agent creating the artifact
            artifact_type: Type of artifact (document, code, data, etc.)
            artifact_id: Optional ID for the artifact (generated if not provided)
            metadata: Additional metadata for the artifact
            
        Returns:
            ID of the created artifact
        """
        # Create the artifact
        artifact = Artifact(
            name=name,
            content=content,
            artifact_type=artifact_type,
            creator_id=creator_id,
            artifact_id=artifact_id,
            metadata=metadata
        )
        
        # Add to workspace
        self.artifacts[artifact.artifact_id] = artifact
        
        # Log the activity
        self._log_activity(
            action="create_artifact",
            artifact_id=artifact.artifact_id,
            agent_id=creator_id,
            metadata={
                "artifact_type": artifact_type,
                "artifact_name": name
            }
        )
        
        return artifact.artifact_id
        
    def update_artifact(
        self,
        artifact_id: str,
        content: Any,
        editor_id: str,
        comment: str = "",
        metadata_updates: Dict[str, Any] = None
    ) -> int:
        """Update an existing artifact
        
        Args:
            artifact_id: ID of the artifact to update
            content: New content for the artifact
            editor_id: ID of the agent making the update
            comment: Optional comment about the changes
            metadata_updates: Optional updates to metadata
            
        Returns:
            New version number
            
        Raises:
            ValueError: If artifact ID does not exist
        """
        if artifact_id not in self.artifacts:
            raise ValueError(f"Artifact with ID {artifact_id} not found")
            
        # Update the artifact
        artifact = self.artifacts[artifact_id]
        new_version = artifact.update(
            new_content=content,
            editor_id=editor_id,
            comment=comment,
            metadata_updates=metadata_updates
        )
        
        # Log the activity
        self._log_activity(
            action="update_artifact",
            artifact_id=artifact_id,
            agent_id=editor_id,
            metadata={
                "new_version": new_version,
                "comment": comment
            }
        )
        
        return new_version
        
    def get_artifact(
        self,
        artifact_id: str,
        version: int = None
    ) -> Dict[str, Any]:
        """Get an artifact's content and metadata
        
        Args:
            artifact_id: ID of the artifact to retrieve
            version: Optional specific version to retrieve
            
        Returns:
            Dictionary with artifact data
            
        Raises:
            ValueError: If artifact ID does not exist
        """
        if artifact_id not in self.artifacts:
            raise ValueError(f"Artifact with ID {artifact_id} not found")
            
        artifact = self.artifacts[artifact_id]
        
        # Return specific version if requested
        if version is not None:
            try:
                version_data = artifact.get_version(version)
                return {
                    "artifact_id": artifact_id,
                    "name": artifact.name,
                    "artifact_type": artifact.artifact_type,
                    "creator_id": artifact.creator_id,
                    **version_data
                }
            except ValueError as e:
                raise ValueError(f"Version {version} of artifact {artifact_id} not found")
                
        # Return current version
        return artifact.to_dict()
        
    def get_artifact_history(self, artifact_id: str) -> List[Dict[str, Any]]:
        """Get complete version history of an artifact
        
        Args:
            artifact_id: ID of the artifact
            
        Returns:
            List of all versions from oldest to newest
            
        Raises:
            ValueError: If artifact ID does not exist
        """
        if artifact_id not in self.artifacts:
            raise ValueError(f"Artifact with ID {artifact_id} not found")
            
        return self.artifacts[artifact_id].get_history()
        
    def delete_artifact(
        self,
        artifact_id: str,
        agent_id: str,
        permanent: bool = False
    ) -> bool:
        """Delete an artifact from the workspace
        
        Args:
            artifact_id: ID of the artifact to delete
            agent_id: ID of the agent requesting deletion
            permanent: Whether to permanently delete (True) or archive (False)
            
        Returns:
            True if successfully deleted
            
        Raises:
            ValueError: If artifact ID does not exist
        """
        if artifact_id not in self.artifacts:
            raise ValueError(f"Artifact with ID {artifact_id} not found")
            
        if permanent:
            # Permanently delete
            del self.artifacts[artifact_id]
        else:
            # Archive by marking in metadata
            self.artifacts[artifact_id].metadata["archived"] = True
            self.artifacts[artifact_id].metadata["archived_at"] = time.time()
            self.artifacts[artifact_id].metadata["archived_by"] = agent_id
            
        # Log the activity
        self._log_activity(
            action="delete_artifact",
            artifact_id=artifact_id,
            agent_id=agent_id,
            metadata={"permanent": permanent}
        )
        
        return True
        
    def get_artifacts_by_type(self, artifact_type: str) -> Dict[str, Artifact]:
        """Get all artifacts of a specific type
        
        Args:
            artifact_type: Type of artifacts to filter by
            
        Returns:
            Dictionary of artifacts of the specified type
        """
        return {
            id: artifact for id, artifact in self.artifacts.items()
            if artifact.artifact_type == artifact_type 
            and not artifact.metadata.get("archived", False)
        }
        
    def get_artifacts_by_creator(self, creator_id: str) -> Dict[str, Artifact]:
        """Get all artifacts created by a specific agent
        
        Args:
            creator_id: ID of the creator agent
            
        Returns:
            Dictionary of artifacts created by the specified agent
        """
        return {
            id: artifact for id, artifact in self.artifacts.items()
            if artifact.creator_id == creator_id
            and not artifact.metadata.get("archived", False)
        }
        
    def search_artifacts(
        self,
        query: Dict[str, Any]
    ) -> Dict[str, Artifact]:
        """Search for artifacts matching criteria
        
        Args:
            query: Dictionary of criteria to match
            
        Returns:
            Dictionary of matching artifacts
        """
        results = {}
        
        for artifact_id, artifact in self.artifacts.items():
            # Skip archived artifacts
            if artifact.metadata.get("archived", False):
                continue
                
            # Check each query parameter
            match = True
            for key, value in query.items():
                # Handle special keys like content_contains
                if key == "content_contains":
                    if isinstance(artifact.content, str):
                        if value not in artifact.content:
                            match = False
                            break
                    elif isinstance(artifact.content, dict):
                        # Search within all string values in the dict
                        found = False
                        for content_val in artifact.content.values():
                            if isinstance(content_val, str) and value in content_val:
                                found = True
                                break
                        if not found:
                            match = False
                            break
                # Handle metadata queries
                elif key.startswith("metadata."):
                    metadata_key = key.split(".", 1)[1]
                    if artifact.metadata.get(metadata_key) != value:
                        match = False
                        break
                # Direct attribute matching
                elif hasattr(artifact, key) and getattr(artifact, key) != value:
                    match = False
                    break
                    
            if match:
                results[artifact_id] = artifact
                
        return results
        
    def _log_activity(
        self,
        action: str,
        artifact_id: str = None,
        agent_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Log an activity in the workspace
        
        Args:
            action: Action being performed
            artifact_id: ID of the artifact involved (if any)
            agent_id: ID of the agent performing the action
            metadata: Additional information about the activity
        """
        activity = {
            "timestamp": time.time(),
            "action": action,
            "workspace_id": self.workspace_id
        }
        
        if artifact_id:
            activity["artifact_id"] = artifact_id
            
        if agent_id:
            activity["agent_id"] = agent_id
            
        if metadata:
            activity["metadata"] = metadata
            
        self.activities.append(activity) 