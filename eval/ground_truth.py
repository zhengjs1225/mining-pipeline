"""
20 ground truth Q&A pairs for mining intelligence evaluation.

Each entry contains:
- id: unique identifier
- question: natural language question (mixed zh/en)
- expected_answer: ground truth answer (can be brief bullet points)
- relevant_sources: list of source identifiers that should contain the answer
- category: news | policy | price
- language: zh | en
- keywords: key terms that retrieved documents MUST contain for recall@k
"""

GROUND_TRUTH = [
    # ── Policy Questions (7) ──────────────────────────
    {
        "id": "gt_001",
        "question": "近7天澳洲锂出口政策有何变化？",
        "expected_answer": "澳大利亚政府近期更新了关键矿产战略，锂作为核心电池材料受到重点关注。澳洲政府鼓励下游加工产业发展，减少原矿出口依赖。",
        "relevant_sources": ["disr_au"],
        "category": "policy",
        "language": "zh",
        "keywords": ["锂", "lithium", "澳洲", "Australia", "出口", "export", "关键矿产", "critical mineral"],
    },
    {
        "id": "gt_002",
        "question": "What are the latest critical mineral policy updates from Australia regarding rare earths?",
        "expected_answer": "Australia's Critical Minerals Strategy 2023-2030 identifies rare earth elements as strategic priority minerals, with funding allocated for processing facilities and supply chain diversification away from China dependence.",
        "relevant_sources": ["disr_au"],
        "category": "policy",
        "language": "en",
        "keywords": ["rare earth", "Australia", "critical mineral", "strategy", "processing"],
    },
    {
        "id": "gt_003",
        "question": "中国稀土集团最近发布了哪些关于出口管制的政策？",
        "expected_answer": "中国稀土集团发布了关于稀土生产和出口配额的公告，涉及开采总量控制指标和出口合规要求。",
        "relevant_sources": ["rare_earth_cn"],
        "category": "policy",
        "language": "zh",
        "keywords": ["稀土", "出口", "配额", "管制", "中国稀土集团"],
    },
    {
        "id": "gt_004",
        "question": "澳洲政府对关键矿产下游加工有什么激励措施？",
        "expected_answer": "澳大利亚政府通过Critical Minerals Facility和National Reconstruction Fund提供资金支持，鼓励在澳洲境内建设锂、稀土、钴等关键矿产的加工和精炼设施。",
        "relevant_sources": ["disr_au"],
        "category": "policy",
        "language": "zh",
        "keywords": ["Australia", "processing", "downstream", "funding", "incentive", "critical mineral"],
    },
    {
        "id": "gt_005",
        "question": "中国在稀土供应链中采取了哪些环境保护措施？",
        "expected_answer": "中国稀土行业加强了环保监管，要求矿山企业达到排放标准，推进绿色矿山建设，对非法开采和环境污染实施严格处罚。",
        "relevant_sources": ["rare_earth_cn"],
        "category": "policy",
        "language": "zh",
        "keywords": ["稀土", "环保", "环境", "监管", "绿色"],
    },
    {
        "id": "gt_006",
        "question": "Australia's critical minerals strategy and its impact on lithium supply chain diversification",
        "expected_answer": "Australia's strategy aims to move beyond raw mineral exports to downstream processing, partnering with allies (US, Japan, Korea, EU) to build alternative supply chains, reducing concentration risk in critical mineral processing.",
        "relevant_sources": ["disr_au"],
        "category": "policy",
        "language": "en",
        "keywords": ["Australia", "lithium", "supply chain", "diversification", "critical mineral", "strategy"],
    },
    {
        "id": "gt_007",
        "question": "中国稀土集团2024-2025年的生产指标和战略规划",
        "expected_answer": "中国稀土集团按照国家下达的稀土开采和冶炼分离总量控制指标组织生产，推进资源整合和产业链延伸。",
        "relevant_sources": ["rare_earth_cn"],
        "category": "policy",
        "language": "zh",
        "keywords": ["稀土", "生产", "指标", "规划", "战略", "总量控制"],
    },

    # ── News Questions (7) ────────────────────────────
    {
        "id": "gt_008",
        "question": "What are the latest copper mining developments covered by Mining.com?",
        "expected_answer": "Recent copper mining developments include new project approvals, production updates from major mines (Escondida, Grasberg), price movements driven by supply concerns and energy transition demand, and M&A activity in the copper sector.",
        "relevant_sources": ["mining_com", "sp_global_mining"],
        "category": "news",
        "language": "en",
        "keywords": ["copper", "mining", "production", "mine", "project"],
    },
    {
        "id": "gt_009",
        "question": "最近镍矿开采行业有哪些重大并购或投资新闻？",
        "expected_answer": "镍矿行业近期有印度尼西亚镍加工投资增加、电动汽车电池级镍需求增长、以及主要矿业公司在镍资产上的并购活动。",
        "relevant_sources": ["mining_com", "sp_global_mining"],
        "category": "news",
        "language": "zh",
        "keywords": ["nickel", "镍", "M&A", "investment", "acquisition", "merger"],
    },
    {
        "id": "gt_010",
        "question": "Zinc market outlook and mine supply disruptions in 2024-2025",
        "expected_answer": "Zinc market faces supply constraints from mine closures and grade declines, while demand from galvanizing and infrastructure remains steady. Treatment charges have declined reflecting tighter concentrate supply.",
        "relevant_sources": ["mining_com", "sp_global_mining", "lme"],
        "category": "news",
        "language": "en",
        "keywords": ["zinc", "supply", "mine", "production", "outlook", "concentrate"],
    },
    {
        "id": "gt_011",
        "question": "铁矿石价格最近走势如何？主要受什么因素影响？",
        "expected_answer": "铁矿石价格受中国钢铁产量、港口库存水平、四大矿山发货量以及中国房地产和基建需求影响。近期价格波动反映了需求预期变化。",
        "relevant_sources": ["steel_union", "mining_com"],
        "category": "news",
        "language": "zh",
        "keywords": ["铁矿石", "iron ore", "价格", "price", "钢铁", "steel"],
    },
    {
        "id": "gt_012",
        "question": "Latest ESG and sustainability initiatives in the global mining industry",
        "expected_answer": "Mining companies are increasing ESG commitments including net-zero targets, renewable energy adoption at mine sites, water stewardship programs, tailings management improvements, and community engagement frameworks.",
        "relevant_sources": ["mining_com", "sp_global_mining"],
        "category": "news",
        "language": "en",
        "keywords": ["ESG", "sustainability", "environmental", "net zero", "renewable", "community"],
    },
    {
        "id": "gt_013",
        "question": "S&P Global Mining最近关于关键矿产供应链的分析报道",
        "expected_answer": "S&P Global分析了关键矿产供应链的集中度风险，中国在稀土、石墨等矿产加工环节的主导地位，以及西方国家和企业推动供应链多元化的努力。",
        "relevant_sources": ["sp_global_mining"],
        "category": "news",
        "language": "zh",
        "keywords": ["supply chain", "供应链", "critical mineral", "关键矿产", "S&P"],
    },
    {
        "id": "gt_014",
        "question": "Recent copper price movements and the impact of energy transition demand",
        "expected_answer": "Copper prices are supported by energy transition demand (EVs, renewable energy, grid infrastructure) while facing short-term headwinds from global economic uncertainty. Long-term supply deficit is expected as new mine development lags demand growth.",
        "relevant_sources": ["lme", "mining_com", "sp_global_mining"],
        "category": "news",
        "language": "en",
        "keywords": ["copper", "price", "energy transition", "demand", "EV", "supply deficit"],
    },

    # ── Price Questions (6) ───────────────────────────
    {
        "id": "gt_015",
        "question": "LME铜价最近30天走势及主要驱动因素",
        "expected_answer": "LME铜价在最近30天内的走势受全球宏观情绪、美元走势、中国需求预期和全球铜矿供应中断等因素影响。铜价在$8,000-9,000/吨区间波动。",
        "relevant_sources": ["lme"],
        "category": "price",
        "language": "zh",
        "keywords": ["LME", "铜", "copper", "价格", "price"],
    },
    {
        "id": "gt_016",
        "question": "What is the current LME nickel price trend and inventory situation?",
        "expected_answer": "LME nickel prices have been under pressure from increased Indonesian supply and slowing EV battery demand growth. LME warehouse inventories have been rebuilding from historic lows.",
        "relevant_sources": ["lme"],
        "category": "price",
        "language": "en",
        "keywords": ["nickel", "LME", "price", "inventory", "Indonesia", "supply"],
    },
    {
        "id": "gt_017",
        "question": "SHFE碳酸锂期货价格近期走势如何？",
        "expected_answer": "SHFE碳酸锂期货价格反映了中国锂市场供需格局，近期受新能源汽车销量、锂盐厂开工率和库存水平影响，价格波动较大。",
        "relevant_sources": ["shfe"],
        "category": "price",
        "language": "zh",
        "keywords": ["碳酸锂", "锂", "lithium", "SHFE", "期货", "价格"],
    },
    {
        "id": "gt_018",
        "question": "LME zinc price comparison: recent performance vs copper and nickel",
        "expected_answer": "Zinc has underperformed copper due to weaker demand from construction sector, while copper benefits from energy transition themes. Nickel faces oversupply from Indonesia. Zinc supply constraints from mine closures provide some price support.",
        "relevant_sources": ["lme"],
        "category": "price",
        "language": "en",
        "keywords": ["zinc", "copper", "nickel", "LME", "price", "comparison", "performance"],
    },
    {
        "id": "gt_019",
        "question": "Mysteel铁矿石价格指数与钢材价格的关系分析",
        "expected_answer": "Mysteel铁矿石价格指数与螺纹钢等成材价格高度相关，铁矿石成本占钢材生产成本的40-50%。钢价上涨通常带动铁矿价格，但需关注钢厂利润和限产政策。",
        "relevant_sources": ["steel_union"],
        "category": "price",
        "language": "zh",
        "keywords": ["铁矿石", "iron ore", "Mysteel", "钢材", "steel", "价格", "price index"],
    },
    {
        "id": "gt_020",
        "question": "Lithium carbonate price forecast and battery metals market outlook for the next quarter",
        "expected_answer": "Lithium carbonate prices are expected to stabilize after significant correction, supported by EV adoption growth and battery manufacturing capacity expansion. Supply response from new projects may cap upside. Long-term demand fundamentals remain strong.",
        "relevant_sources": ["shfe", "mining_com", "disr_au"],
        "category": "price",
        "language": "en",
        "keywords": ["lithium", "price", "forecast", "battery", "EV", "carbonate", "outlook"],
    },
]
