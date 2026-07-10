"""
Seed data generator for sources that may be unreachable in certain network
environments (e.g., Chinese government sites from WSL, Australian gov from
some regions, or login-walled price feeds).

This ensures the pipeline always produces a working corpus for testing
and demonstration, even when scraping fails.

All seed data is labeled with metadata["seed"] = True so it can be
distinguished from real scraped data.
"""

import random
from datetime import datetime, timedelta, timezone
from typing import List

from .config import MiningDocument


def _uid(source: str, idx: int) -> str:
    """Deterministic ID for seed data."""
    import hashlib
    return hashlib.sha256(f"seed:{source}:{idx}".encode()).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── China Rare Earth Group Seed Data ─────────────────────

RARE_EARTH_CN_SEEDS = [
    {
        "title": "中国稀土集团召开2025年工作会议 部署全年重点任务",
        "content": """中国稀土集团有限公司于近日召开2025年度工作会议。会议总结了2024年工作成效，分析当前稀土行业发展形势，部署2025年重点工作任务。

会议强调，要深入贯彻落实国家稀土产业政策，坚持"保护性开发、高值化利用"方针，持续推进稀土开采总量控制，严格落实出口管制政策，维护稀土供应链安全。

重点任务包括：
1. 严格执行国家稀土开采和冶炼分离总量控制指标
2. 推进绿色矿山建设，实现废水零排放
3. 加快稀土新材料研发和产业化应用
4. 深化国际合作，拓展稀土高端应用市场
5. 加强稀土资源综合回收利用

会议指出，中国作为全球最大的稀土生产国和出口国，将继续发挥稀土供应链优势，同时推动产业向高端化、绿色化方向发展。""",
    },
    {
        "title": "中国稀土集团发布2025年第一批稀土开采总量控制指标",
        "content": """根据自然资源部和工信部联合通知，中国稀土集团发布2025年第一批稀土开采总量控制指标。

本批次指标分配如下：
- 岩矿型稀土（轻稀土）开采指标：×××××吨
- 离子型稀土（中重稀土）开采指标：×××××吨
- 冶炼分离指标：×××××吨

集团要求各所属企业严格按指标组织生产，严禁超指标开采。同时加强环保监管，确保矿山生态环境恢复治理达标。

此次指标发布体现了国家对稀土资源实行保护性开发的政策导向，有助于维护稀土市场供需平衡，保障国家战略资源安全。""",
    },
    {
        "title": "中国稀土集团与江西省签署战略合作协议 推动稀土产业集群发展",
        "content": """中国稀土集团与江西省人民政府签署战略合作框架协议，双方将在稀土资源整合、深加工产业链建设、科技创新平台共建等方面深化合作。

江西省是中国离子型稀土资源最丰富的省份。根据协议，双方将：
- 共同推进赣州稀土资源高效开发利用
- 建设国家级稀土功能材料创新中心
- 打造稀土永磁材料产业集群
- 推动稀土在新能源汽车、风力发电等领域的应用

此次合作有助于巩固中国在中重稀土领域的全球主导地位，推动稀土产业向价值链高端攀升。""",
    },
    {
        "title": "商务部发布稀土出口管制新规 加强战略性资源管理",
        "content": """商务部会同海关总署发布了稀土出口管制相关措施调整公告。新规对部分稀土产品实施出口许可证管理，涉及镝、铽、钐等中重稀土元素及其合金产品。

主要调整内容包括：
- 扩大出口管制稀土产品目录范围
- 强化最终用户和最终用途审查
- 加强对稀土永磁体等下游产品的出口监控
- 建立稀土出口合规管理体系

商务部表示，此次调整是基于维护国家安全和履行国际义务的需要，符合国际通行做法。中国将继续保障全球稀土供应链稳定，同时坚决维护国家战略利益。

业内人士分析认为，此举将影响全球稀土供应格局，推动稀土价格中枢上移。""",
    },
    {
        "title": "中国稀土集团推进绿色矿山建设 矿山水循环利用率达95%",
        "content": """中国稀土集团在2025年环境日发布绿色矿山建设成果报告。报告显示，集团所属矿山企业全面推进绿色矿山建设，取得显著成效。

关键环保指标：
- 矿山水循环利用率：95.2%
- 矿山土地复垦率：88.6%
- 选矿废水零排放达标率：100%
- 固体废物综合利用率：76.3%

集团投入专项资金用于环保设施升级改造，推广无铵工艺替代传统铵盐工艺，从源头减少氨氮污染。同时建立了矿山生态环境监测系统，实现环境风险实时预警。

集团相关负责人表示，绿色矿山建设是稀土行业可持续发展的必由之路，集团将继续加大环保投入，打造行业绿色发展标杆。""",
    },
]

# ── Australia DISR Seed Data ─────────────────────────────

DISR_AU_SEEDS = [
    {
        "title": "Australia's Critical Minerals Strategy 2023-2030 — Implementation Update",
        "content": """The Australian Government has released an implementation update for the Critical Minerals Strategy 2023-2030, outlining progress on key initiatives to grow Australia's critical minerals sector.

Key achievements to date:
- $4 billion in government funding committed through the Critical Minerals Facility and National Reconstruction Fund
- $500 million for the Northern Australia Infrastructure Facility (NAIF) to support critical minerals projects
- Establishment of the Critical Minerals Office to coordinate policy across government
- Bilateral agreements signed with Japan, Korea, India, the UK, and the EU on critical mineral supply chain cooperation
- Streamlined approvals for critical minerals projects under the EPBC Act

The Strategy identifies 26 critical minerals including lithium, cobalt, nickel, rare earth elements, graphite, and vanadium as priorities for development.

Australia aims to become a globally significant producer of processed critical minerals by 2030, moving beyond raw material exports to capture more value from downstream processing. This includes supporting the development of lithium hydroxide refining, rare earth separation, and battery cathode precursor manufacturing facilities.

The update also highlights the importance of working with First Nations communities and ensuring that critical minerals development delivers shared benefits through Indigenous Land Use Agreements and local employment. The government expects the critical minerals sector to support 10,000 new jobs by 2030. Additionally, $50 million has been allocated to the Critical Minerals R&D Fund to accelerate technology development in mineral processing and recycling. The CSIRO's Critical Minerals Roadmap provides a framework for prioritizing research investment across the value chain.
""",
    },
    {
        "title": "Australia-Japan Critical Minerals Partnership — Lithium Supply Chain Cooperation",
        "content": """Australia and Japan have deepened their critical minerals partnership, with a focus on lithium supply chain cooperation. The partnership aims to diversify lithium processing away from concentration in a single country and build a more resilient supply chain for battery materials.

Key elements of the cooperation include:
- Joint investment in Australian lithium hydroxide processing facilities
- Japanese offtake agreements for Australian lithium spodumene concentrate
- Technology collaboration on direct lithium extraction (DLE) technologies
- Workforce training and exchange programs

Japan is the second-largest producer of electric vehicles globally and requires a stable supply of battery-grade lithium. Australia, as the world's largest lithium producer (accounting for approximately 50% of global production), is a natural partner.

The partnership is part of the broader Quad (US-Japan-Australia-India) critical minerals cooperation framework. It also supports the US Inflation Reduction Act's requirement for EV battery materials to be sourced from Free Trade Agreement countries, enhancing the competitiveness of Japanese automakers in the US market.

The governments are exploring the potential for joint rare earth processing as a next phase of cooperation, with Lynas Rare Earth's processing facility in Kalgoorlie serving as a model for future projects. In a related development, the Japanese government announced a 200 billion yen fund to support overseas mineral processing investments, with Australia identified as a priority destination. Additionally, the partnership includes provisions for information sharing on mineral resource assessments and the co-development of processing technologies that meet the highest environmental standards.
""",
    },
    {
        "title": "Australia's Critical Minerals List Updated — Graphite and High-Purity Alumina Added",
        "content": """The Australian Government has updated its Critical Minerals List, adding high-purity alumina (HPA) and upgrading graphite from a strategic to a critical designation. The updated list now includes 30 minerals deemed critical to Australia's economic and strategic interests.

The update reflects:
- Growing demand for HPA in LED lighting, semiconductor substrates, and lithium-ion battery separators
- Graphite's essential role in lithium-ion battery anodes
- Supply chain concentration risks, with China currently dominant in graphite processing
- Emerging applications in defense and aerospace technologies

Resources Minister noted that the updated list will guide government investment priorities through the $4 billion Critical Minerals Facility. Projects involving newly listed minerals will be eligible for streamlined approvals and financial support.

Australia has significant undeveloped graphite resources in South Australia, Western Australia, and Queensland. Several projects are advancing toward production:
- Renascor Resources' Siviour graphite project (SA)
- International Graphite's Springdale project (WA)
- Syrah Resources' Balama graphite mine (Mozambique, with processing in Louisiana, USA)

The government has also established a Critical Minerals Prospectus to attract international investment in Australian critical minerals projects. The prospectus highlights 52 investment-ready projects across the country. An interactive digital platform providing detailed geological data and infrastructure information is available to assist potential investors in evaluating project opportunities across Australia's critical minerals provinces.
""",
    },
    {
        "title": "Western Australia's Lithium Royalty — New Fiscal Framework for Battery Minerals",
        "content": """The Western Australian Government has introduced a new fiscal framework for lithium and other battery minerals, including a modified royalty regime designed to capture more value from the state's growing lithium industry while maintaining competitiveness for new project development.

Key features of the new framework:
- Tiered royalty rates based on the level of downstream processing conducted in WA
- Reduced royalties for lithium hydroxide and other processed products produced domestically
- Additional royalty discount for projects that utilize renewable energy for processing
- A$200 million Battery Materials Processing Fund to co-invest in downstream facilities

WA currently produces over 50% of the world's lithium from hard-rock spodumene mines, primarily in the Pilbara and Goldfields regions. However, most lithium concentrate is exported to China for processing into battery-grade chemicals.

The new framework aims to incentivize onshore processing, creating an integrated lithium value chain from mine to battery material within Western Australia. The government estimates this could create 5,000 direct jobs and generate A$10 billion in additional annual export revenue by 2030.

The Minerals Council of Australia welcomed the initiative but called for complementary federal tax incentives and streamlined environmental approvals to maximize the policy's effectiveness. The framework also includes provisions for strategic stockpiling of critical battery minerals to manage supply disruptions. A supply chain resilience assessment will be conducted annually, with the first report due by year-end. Industry consultation on the detailed implementation guidelines is open until the end of the quarter.
""",
    },
    {
        "title": "Australia's Rare Earth Processing Ambitions — Lynas and Iluka Lead the Way",
        "content": """Australia's ambition to become a major rare earth processing hub is gaining momentum, led by Lynas Rare Earths and Iluka Resources. The Australian Government is providing significant financial support to establish a sovereign rare earth processing capability.

Lynas Rare Earths, the world's largest non-Chinese rare earth producer, operates:
- Mt Weld mine in Western Australia (one of the world's highest-grade rare earth deposits)
- Kalgoorlie cracking and leaching plant (newly commissioned, A$575 million investment)
- Lynas Malaysia advanced processing facility (producing separated rare earth oxides)
- Planned US processing facility in Texas (supported by US Department of Defense funding)

Iluka Resources is developing Australia's first fully integrated rare earth refinery at Eneabba, Western Australia:
- A$1.2 billion project, with A$1.05 billion government loan through the Critical Minerals Facility
- Will process monazite feedstock to produce separated rare earth oxides
- Expected production capacity: 17,500 tonnes per annum of rare earth oxides
- Target markets: neodymium-praseodymium (NdPr) for permanent magnets, plus dysprosium and terbium

The Australian Government has also commissioned a Rare Earth Supply Chain Study to identify further opportunities for downstream processing and value addition. The study will examine the feasibility of establishing Australian production of rare earth permanent magnets, targeting the growing demand from EVs and wind turbines. A parallel workforce development initiative aims to train 500 specialist technicians and engineers over the next five years to support the rare earth processing industry.
""",
    },
]

# ── Price Seed Data ──────────────────────────────────────

def _generate_lme_seeds(num: int = 200) -> List[dict]:
    """Generate structured LME price documents."""
    seeds = []
    metals = ["Copper", "Zinc", "Nickel"]
    tickers = {"Copper": "CA", "Zinc": "ZS", "Nickel": "NI"}
    base_prices = {"Copper": 8950.0, "Zinc": 2850.0, "Nickel": 16800.0}

    for i in range(num):
        metal = metals[i % 3]
        date = datetime.now(timezone.utc) - timedelta(days=i // 3)
        date_str = date.strftime("%Y-%m-%d")

        # Add random price variation ±5%
        base = base_prices[metal]
        price = base * (1 + random.uniform(-0.05, 0.05))

        content = f"""LME {metal} ({tickers[metal]}) Daily Price Report
Date: {date_str}
Exchange: London Metal Exchange (LME)
Metal: {metal}
Ticker: {tickers[metal]}
Category: Base Metals
Settlement Price: ${price:,.2f} USD/tonne
Volume: {random.randint(5000, 25000):,} lots
Open Interest: {random.randint(150000, 350000):,} lots

This is the daily LME {metal} price record. LME {metal} prices are global benchmarks for base metals trading, reflecting supply-demand dynamics, global inventory levels, and macroeconomic conditions affecting the mining sector.
Key market factors:
- Global exchange inventory levels and warehouse movements
- Chinese import demand and SHFE arbitrage window
- US dollar index and macroeconomic sentiment
- Supply disruptions at major mining operations
- Energy transition demand for electrification metals"""

        seeds.append({
            "title": f"LME {metal} Price — {date_str}",
            "content": content,
            "url": f"https://www.lme.com/en/metals/non-ferrous/lme-{metal.lower()}",
            "published_at": date.isoformat(),
            "metadata": {
                "ticker": tickers[metal],
                "metal": metal.lower(),
                "exchange": "LME",
                "date": date_str,
                "price_data": {
                    "current_price": round(price, 2),
                    "volume": random.randint(5000, 25000),
                    "open_interest": random.randint(150000, 350000),
                },
            },
        })

    return seeds


def _generate_shfe_seeds(num: int = 200) -> List[dict]:
    """Generate structured SHFE lithium futures documents."""
    seeds = []
    base_price = 105000.0  # CNY/tonne for lithium carbonate

    for i in range(num):
        date = datetime.now(timezone.utc) - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        price = base_price * (1 + random.uniform(-0.08, 0.08))

        content = f"""SHFE 碳酸锂期货 (Lithium Carbonate Futures) 每日行情
日期: {date_str}
交易所: 上海期货交易所 (Shanghai Futures Exchange)
品种: 碳酸锂 (Lithium Carbonate)
合约代码: LC
交易单位: 1吨/手
结算价: ¥{price:,.0f} CNY/吨
成交量: {random.randint(50000, 200000):,} 手
持仓量: {random.randint(80000, 300000):,} 手

碳酸锂是动力电池核心原材料，SHFE碳酸锂期货是全球锂产业链的重要定价参考。
锂价受新能源汽车销量、盐湖/锂辉石供给、储能政策、下游电池厂商补库节奏等多重因素影响。

中国是全球最大的锂消费国和加工国，SHFE锂期货价格反映了亚太地区锂市场供需格局。
主要关注因素：
- 新能源汽车月度销量数据
- 锂盐厂开工率和库存水平
- 澳洲锂辉石和南美盐湖供给变化
- 储能市场需求增长趋势
- 电池厂商采购策略和库存周期"""

        seeds.append({
            "title": f"SHFE 碳酸锂期货价格 — {date_str}",
            "content": content,
            "url": "https://www.shfe.com.cn",
            "published_at": date.isoformat(),
            "metadata": {
                "ticker": "LC",
                "metal": "lithium",
                "exchange": "SHFE",
                "date": date_str,
                "contract": "碳酸锂 (Lithium Carbonate)",
            },
        })

    return seeds


def _generate_steel_union_seeds(num: int = 200) -> List[dict]:
    """Generate structured Mysteel iron ore price documents."""
    seeds = []
    base_price = 125.0  # USD/tonne

    for i in range(num):
        date = datetime.now(timezone.utc) - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        price = base_price * (1 + random.uniform(-0.06, 0.06))

        content = f"""Mysteel 铁矿石价格指数 (Iron Ore Price Index) 每日报告
日期: {date_str}
发布机构: 上海钢联 (Mysteel / Shanghai Steel Union)
品种: 铁矿石 (Iron Ore)
品位: 62% Fe (基准品位)
价格指数: ${price:.2f} USD/干吨
港口现货: ¥{price * 7.2:.0f} CNY/湿吨

Mysteel铁矿石价格指数是中国钢铁行业广泛使用的铁矿石定价基准。
铁矿石价格受以下因素影响：
- 全球粗钢产量变化（特别是中国）
- 四大矿山(力拓、必和必拓、FMG、淡水河谷)发货量
- 中国主要港口铁矿石库存水平
- 环保限产政策影响
- 房地产和基建用钢需求
- 海运费率变化

中国是全球最大的铁矿石进口国，占全球海运铁矿石贸易量的70%以上。
澳大利亚和巴西是中国铁矿石进口的主要来源国。"""

        seeds.append({
            "title": f"Mysteel 铁矿石价格指数 — {date_str}",
            "content": content,
            "url": "https://www.mysteel.com",
            "published_at": date.isoformat(),
            "metadata": {
                "ticker": "IO",
                "metal": "iron_ore",
                "exchange": "Mysteel",
                "date": date_str,
                "index": "Mysteel Iron Ore Price Index",
            },
        })

    return seeds


# ── Master seed data generator ───────────────────────────

def generate_all_seeds() -> List[MiningDocument]:
    """Generate seed data for ALL sources to ensure complete coverage."""
    docs = []

    # Policy seeds (Rare Earth CN + DISR AU)
    for i, seed in enumerate(RARE_EARTH_CN_SEEDS):
        docs.append(MiningDocument(
            id=_uid("rare_earth_cn", i),
            source="rare_earth_cn",
            category="policy",
            title=seed["title"],
            content=seed["content"],
            url=f"https://www.creg.com.cn/seed/{i}",
            published_at=(datetime.now(timezone.utc) - timedelta(days=i * 5)).isoformat(),
            language="zh",
            metadata={"minerals_mentioned": ["稀土", "rare earth"], "policy_types": ["export_quota", "production_cap", "environmental"], "seed": True},
            ingested_at=_now(),
        ))

    for i, seed in enumerate(DISR_AU_SEEDS):
        docs.append(MiningDocument(
            id=_uid("disr_au", i),
            source="disr_au",
            category="policy",
            title=seed["title"],
            content=seed["content"],
            url=f"https://www.industry.gov.au/seed/{i}",
            published_at=(datetime.now(timezone.utc) - timedelta(days=i * 6)).isoformat(),
            language="en",
            metadata={"minerals_mentioned": ["lithium", "rare earth", "graphite", "cobalt", "nickel"], "policy_types": ["investment", "processing", "supply_chain"], "seed": True},
            ingested_at=_now(),
        ))

    # Price seeds
    for seed in _generate_lme_seeds(200):
        docs.append(MiningDocument(
            id=_uid("lme", len(docs)),
            source="lme",
            category="price",
            title=seed["title"],
            content=seed["content"],
            url=seed["url"],
            published_at=seed["published_at"],
            language="en",
            metadata={**seed["metadata"], "seed": True},
            ingested_at=_now(),
        ))

    for seed in _generate_shfe_seeds(200):
        docs.append(MiningDocument(
            id=_uid("shfe", len(docs)),
            source="shfe",
            category="price",
            title=seed["title"],
            content=seed["content"],
            url=seed["url"],
            published_at=seed["published_at"],
            language="zh",
            metadata={**seed["metadata"], "seed": True},
            ingested_at=_now(),
        ))

    for seed in _generate_steel_union_seeds(200):
        docs.append(MiningDocument(
            id=_uid("steel_union", len(docs)),
            source="steel_union",
            category="price",
            title=seed["title"],
            content=seed["content"],
            url=seed["url"],
            published_at=seed["published_at"],
            language="zh",
            metadata={**seed["metadata"], "seed": True},
            ingested_at=_now(),
        ))

    return docs


def generate_source_seed(source: str) -> List[MiningDocument]:
    """Generate seed data for a specific source only."""
    all_seeds = generate_all_seeds()
    return [d for d in all_seeds if d.source == source]
