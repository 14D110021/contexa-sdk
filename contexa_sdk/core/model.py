"""Model module for Contexa SDK."""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from contexa_sdk.core.config import ContexaConfig


class ModelMessage(BaseModel):
    """A message in a conversation."""
    
    role: str
    content: str


class ModelResponse(BaseModel):
    """Response from an LLM."""
    
    content: str
    model: str
    usage: Dict[str, int] = Field(default_factory=dict)
    
    
class EmbeddingResponse(BaseModel):
    """Response from an embedding model."""
    
    embedding: List[float]
    model: str
    usage: Dict[str, int] = Field(default_factory=dict)


class ContexaModel:
    """Framework-agnostic wrapper for language models."""
    
    def __init__(
        self,
        model_name: str,
        config: Optional[ContexaConfig] = None,
        provider: str = "openai",
        model_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a ContexaModel.
        
        Args:
            model_name: Name of the model to use (e.g. "gpt-4o", "claude-3-sonnet")
            config: Configuration for the model
            provider: Model provider (e.g. "openai", "anthropic", "local")
            model_kwargs: Additional keyword arguments to pass to the model
        """
        self.model_name = model_name
        self.config = config or ContexaConfig()
        self.provider = provider
        self.model_kwargs = model_kwargs or {}
        self._client = None
        
    async def generate(
        self, 
        messages: List[ModelMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> ModelResponse:
        """Generate a response from the model.
        
        Args:
            messages: List of messages in the conversation
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum number of tokens to generate
            stop: List of strings to stop generation at
            
        Returns:
            ModelResponse with the generated content
        """
        if self.provider == "openai":
            return await self._generate_openai(
                messages, temperature, max_tokens, stop
            )
        elif self.provider == "anthropic":
            return await self._generate_anthropic(
                messages, temperature, max_tokens, stop
            )
        elif self.provider == "local":
            return await self._generate_local(
                messages, temperature, max_tokens, stop
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
            
    async def _generate_openai(
        self,
        messages: List[ModelMessage],
        temperature: float,
        max_tokens: Optional[int],
        stop: Optional[List[str]],
    ) -> ModelResponse:
        """Generate a response using the OpenAI API."""
        try:
            import openai
        except ImportError:
            raise ImportError(
                "OpenAI package not found. Install with `pip install openai`."
            )
            
        client = openai.AsyncOpenAI(
            api_key=self.config.api_key,
        )
        
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
            **self.model_kwargs,
        )
        
        return ModelResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        )
        
    async def _generate_anthropic(
        self,
        messages: List[ModelMessage],
        temperature: float,
        max_tokens: Optional[int],
        stop: Optional[List[str]],
    ) -> ModelResponse:
        """Generate a response using the Anthropic API."""
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "Anthropic package not found. Install with `pip install anthropic`."
            )
            
        client = anthropic.AsyncAnthropic(
            api_key=self.config.api_key,
        )
        
        # Convert our messages to Anthropic's format
        messages_list = []
        for msg in messages:
            if msg.role == "system":
                # Anthropic handles system differently
                continue
            messages_list.append({"role": msg.role, "content": msg.content})
        
        # Find the system message if any
        system_message = next(
            (m.content for m in messages if m.role == "system"), 
            None
        )
        
        response = await client.messages.create(
            model=self.model_name,
            messages=messages_list,
            system=system_message,
            temperature=temperature,
            max_tokens=max_tokens or 1024,
            stop_sequences=stop or [],
            **self.model_kwargs,
        )
        
        return ModelResponse(
            content=response.content[0].text,
            model=response.model,
            usage=response.usage._asdict() if hasattr(response, "usage") else {},
        )
        
    async def _generate_local(
        self,
        messages: List[ModelMessage],
        temperature: float,
        max_tokens: Optional[int],
        stop: Optional[List[str]],
    ) -> ModelResponse:
        """Generate a response using a local model (llama-cpp-python)."""
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError(
                "llama-cpp-python package not found. "
                "Install with `pip install llama-cpp-python`."
            )
            
        if not hasattr(self, "_local_model"):
            # Initialize the model
            self._local_model = Llama(
                model_path=self.model_name,  # For local, model_name is the path
                **self.model_kwargs,
            )
            
        # Format messages into a prompt
        prompt = ""
        for msg in messages:
            if msg.role == "system":
                prompt += f"<|system|>\n{msg.content}\n"
            elif msg.role == "user":
                prompt += f"<|user|>\n{msg.content}\n"
            elif msg.role == "assistant":
                prompt += f"<|assistant|>\n{msg.content}\n"
        
        prompt += "<|assistant|>\n"
        
        # Generate
        output = self._local_model(
            prompt,
            max_tokens=max_tokens or 512,
            temperature=temperature,
            stop=stop or ["<|user|>", "<|system|>"],
        )
        
        return ModelResponse(
            content=output["choices"][0]["text"],
            model=self.model_name,
            usage={
                "prompt_tokens": output.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": output.get("usage", {}).get("completion_tokens", 0),
                "total_tokens": output.get("usage", {}).get("total_tokens", 0),
            },
        )
        
    async def embed(self, text: str) -> EmbeddingResponse:
        """Generate embeddings for text.
        
        Args:
            text: Text to embed
            
        Returns:
            EmbeddingResponse with the embedding
        """
        if self.provider == "openai":
            return await self._embed_openai(text)
        elif self.provider == "local":
            return await self._embed_local(text)
        else:
            raise ValueError(f"Embedding not supported for provider: {self.provider}")
            
    async def _embed_openai(self, text: str) -> EmbeddingResponse:
        """Generate embeddings using the OpenAI API."""
        try:
            import openai
        except ImportError:
            raise ImportError(
                "OpenAI package not found. Install with `pip install openai`."
            )
            
        client = openai.AsyncOpenAI(
            api_key=self.config.api_key,
        )
        
        response = await client.embeddings.create(
            model=self.model_name,
            input=text,
            **self.model_kwargs,
        )
        
        return EmbeddingResponse(
            embedding=response.data[0].embedding,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        )
        
    async def _embed_local(self, text: str) -> EmbeddingResponse:
        """Generate embeddings using a local model."""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers package not found. "
                "Install with `pip install sentence-transformers`."
            )
            
        if not hasattr(self, "_embedding_model"):
            # Initialize the model
            self._embedding_model = SentenceTransformer(self.model_name)
            
        # Generate embedding
        embedding = self._embedding_model.encode(text)
        
        return EmbeddingResponse(
            embedding=embedding.tolist(),
            model=self.model_name,
            usage={},
        ) 