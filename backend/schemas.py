from pydantic import BaseModel, Field


# --- Auth ---
class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=50)
    password: str = Field(default="", max_length=100)
    nickname: str | None = Field(default=None, max_length=20)


class AuthResponse(BaseModel):
    token: str
    username: str
    user_id: str
    email: str


# --- Market ---
class PlayerInfo(BaseModel):
    player_id: str
    nickname: str
    cash: float
    total_assets: float
    pnl_percent: float


class MarketInfo(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    volume: int
    shares_outstanding: int
    players_online: int


class LeaderboardEntry(BaseModel):
    rank: int
    player_id: str
    nickname: str
    total_assets: float
    pnl_percent: float


# --- Company ---
class CompanyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    industry: str = Field(pattern=r"^(tech|finance|manufacturing|energy|consumer|healthcare)$")


class CompanyResponse(BaseModel):
    id: int
    player_id: str
    name: str
    symbol: str
    industry: str
    industry_name: str = ""
    cash: float
    total_assets: float
    revenue: float
    profit: float
    employees: int
    quarter: int
    alloc_pcts: dict
    current_strategy: str = "balanced"
    tech_points: float = 0.0
    share_price: float
    shares_outstanding: int
    valuation: float = 0.0
    created_at: str = ""


class CompanyRankingEntry(BaseModel):
    rank: int
    player_id: str
    name: str
    symbol: str
    industry: str
    industry_name: str
    market_cap: float
    revenue: float
    profit: float
    share_price: float
    dividend_yield: float = 0.0


class IndustryInfo(BaseModel):
    industry_id: str
    industry_name: str
    industry_desc: str
    cycle: str  # boom / normal / recession
    cycle_name: str
    cycle_desc: str
    companies: list[dict] = []


class CashActionRequest(BaseModel):
    action_type: str
    amount: float = 0
    target_industry: str | None = None


class DecisionRequest(BaseModel):
    decision_type: str
    choice: str


class AllocRequest(BaseModel):
    alloc_pcts: dict
    strategy: str | None = None


class AnnounceRequest(BaseModel):
    title: str = Field(max_length=50)
    content: str = Field(max_length=500)
