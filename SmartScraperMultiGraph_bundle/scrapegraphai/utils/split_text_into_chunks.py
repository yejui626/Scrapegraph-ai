"""
split_text_into_chunks module
"""

from typing import List

from .tokenizer import num_tokens_calculus


def split_text_into_chunks(text: str, chunk_size: int, use_semchunk=True) -> List[str]:
    """
    Splits the text into chunks based on the number of tokens.

    Args:
        text (str): The text to split.
        chunk_size (int): The maximum number of tokens per chunk.

    Returns:
        List[str]: A list of text chunks.
    """

    if use_semchunk:
        from semchunk import chunk

        def count_tokens(text):
            return num_tokens_calculus(text)

        chunk_size = min(chunk_size, int(chunk_size * 0.9))

        chunks = chunk(
            text=text, chunk_size=chunk_size, token_counter=count_tokens, memoize=False
        )
        return chunks

    else:
        tokens = num_tokens_calculus(text)

        if tokens <= chunk_size:
            return [text]

        chunks = []
        current_chunk = []
        current_length = 0

        words = text.split()
        for word in words:
            word_tokens = num_tokens_calculus(word)
            if current_length + word_tokens > chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = word_tokens
            else:
                current_chunk.append(word)
                current_length += word_tokens

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
