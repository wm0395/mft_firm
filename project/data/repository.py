from __future__ import annotations

from project.data.db import DuckDBAccess
from project.data.repository_assets import RepositoryAssetsMixin
from project.data.repository_base import DataRepositoryBase
from project.data.repository_decisions import RepositoryDecisionMixin
from project.data.repository_evaluations import RepositoryEvaluationsMixin
from project.data.repository_market import RepositoryMarketDataMixin
from project.data.repository_hypotheses import RepositoryHypothesesMixin
from project.data.repository_research import RepositoryResearchMixin
from project.data.repository_research_commands import (
    RepositoryResearchCandidateCommandMixin,
    RepositoryResearchProjectCommandMixin,
    RepositoryResearchRunCommandMixin,
)
from project.data.repository_research_lifecycle import (
    RepositoryParameterMixin,
    RepositoryResearchProjectMixin,
    RepositoryResearchRunMixin,
    RepositoryStrategyLifecycleMixin,
)
from project.data.repository_signals import RepositorySignalsMixin
from project.data.repository_trading import RepositoryTradingMixin


class DataRepository(
    DataRepositoryBase,
    RepositoryMarketDataMixin,
    RepositoryAssetsMixin,
    RepositoryHypothesesMixin,
    RepositoryResearchMixin,
    RepositoryResearchRunMixin,
    RepositoryResearchProjectMixin,
    RepositoryParameterMixin,
    RepositoryStrategyLifecycleMixin,
    RepositoryResearchProjectCommandMixin,
    RepositoryResearchRunCommandMixin,
    RepositoryResearchCandidateCommandMixin,
    RepositorySignalsMixin,
    RepositoryEvaluationsMixin,
    RepositoryTradingMixin,
    RepositoryDecisionMixin,
):
    def __init__(self, db: DuckDBAccess) -> None:
        super().__init__(db)
