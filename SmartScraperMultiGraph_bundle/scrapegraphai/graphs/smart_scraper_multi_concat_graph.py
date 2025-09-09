"""
SmartScraperMultiCondGraph Module with ConditionalNode
"""

from copy import deepcopy
from typing import List, Optional, Type

from pydantic import BaseModel

from ..nodes import (
    ConcatAnswersNode,
    ConditionalNode,
    GraphIteratorNode,
    MergeAnswersNode,
)
from ..utils.copy import safe_deepcopy
from .abstract_graph import AbstractGraph
from .base_graph import BaseGraph
from .smart_scraper_graph import SmartScraperGraph


class SmartScraperMultiConcatGraph(AbstractGraph):
    """
    SmartScraperMultiConditionalGraph is a scraping pipeline that scrapes a
    list of URLs and generates answers to a given prompt.

    Attributes:
        prompt (str): The user prompt to search the internet.
        llm_model (dict): The configuration for the language model.
        embedder_model (dict): The configuration for the embedder model.
        headless (bool): A flag to run the browser in headless mode.
        verbose (bool): A flag to display the execution information.
        model_token (int): The token limit for the language model.

    Args:
        prompt (str): The user prompt to search the internet.
        source (List[str]): The source of the graph.
        config (dict): Configuration parameters for the graph.
        schema (Optional[BaseModel]): The schema for the graph output.

    Example:
        >>> smart_scraper_multi_concat_graph = SmartScraperMultiConcatGraph(
        ...     "What is Chioggia famous for?",
        ...     {"llm": {"model": "openai/gpt-3.5-turbo"}}
        ... )
        >>> result = smart_scraper_multi_concat_graph.run()
    """

    def __init__(
        self,
        prompt: str,
        source: List[str],
        config: dict,
        schema: Optional[Type[BaseModel]] = None,
    ):
        self.copy_config = safe_deepcopy(config)
        self.copy_schema = deepcopy(schema)

        super().__init__(prompt, config, source, schema)

    def _create_graph(self) -> BaseGraph:
        """
        Creates the graph of nodes representing the workflow for web scraping and searching,
        including a ConditionalNode to decide between merging or concatenating the results.

        Returns:
            BaseGraph: A graph instance representing the web scraping and searching workflow.
        """

        graph_iterator_node = GraphIteratorNode(
            input="user_prompt & urls",
            output=["results"],
            node_config={
                "graph_instance": SmartScraperGraph,
                "scraper_config": self.copy_config,
            },
            schema=self.copy_schema,
            node_name="GraphIteratorNode",
        )

        conditional_node = ConditionalNode(
            input="results",
            output=["results"],
            node_name="ConditionalNode",
            node_config={"key_name": "results", "condition": "len(results) > 2"},
        )

        merge_answers_node = MergeAnswersNode(
            input="user_prompt & results",
            output=["answer"],
            node_config={"llm_model": self.llm_model, "schema": self.copy_schema},
            node_name="MergeAnswersNode",
        )

        concat_node = ConcatAnswersNode(
            input="results", output=["answer"], node_config={}, node_name="ConcatNode"
        )

        return BaseGraph(
            nodes=[
                graph_iterator_node,
                conditional_node,
                merge_answers_node,
                concat_node,
            ],
            edges=[
                (graph_iterator_node, conditional_node),
                # True node (len(results) > 2)
                (conditional_node, merge_answers_node),
                # False node (len(results) <= 2)
                (conditional_node, concat_node),
            ],
            entry_point=graph_iterator_node,
            graph_name=self.__class__.__name__,
        )

    def run(self) -> str:
        """
        Executes the web scraping and searching process.

        Returns:
            str: The answer to the prompt.
        """

        inputs = {"user_prompt": self.prompt, "urls": self.source}
        self.final_state, self.execution_info = self.graph.execute(inputs)

        return self.final_state.get("answer", "No answer found.")
