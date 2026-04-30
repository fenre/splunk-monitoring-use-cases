# Splunk Monitoring Use Cases — Codebase Diagram

This document visualizes the repository structure, **v7** build pipeline, and data flow (**7,364** use cases).

---

## 1. High-level architecture

```mermaid
flowchart LR
    subgraph sources["Source"]
        CAT["content/cat-*/<br/>_category.json"]
        UC["content/cat-*/<br/>UC-*.json"]
        DATA["data/ regulations,<br/>crosswalks, …"]
        SRC["src/ styles, scripts,<br/>pages, partials"]
        PUB["public/ static"]
    end

    subgraph build["Build"]
        PY["tools/build/build.py<br/>parse + render_*"]
    end

    subgraph output["Output (dist/)"]
        API["api/<br/>catalog-index.json<br/>cat-N.json, v1/…"]
        SITE["browse/, uc/, category/<br/>HTML + JSON twins"]
        ASSET["assets/<br/>fingerprinted JS/CSS<br/>search shards"]
    end

    subgraph app["Runtime"]
        BROW["/browse/ SPA"]
        LOADER["Loader fetches API"]
    end

    CAT --> PY
    UC --> PY
    DATA --> PY
    SRC --> PY
    PUB --> PY
    PY --> API
    PY --> SITE
    PY --> ASSET
    API --> LOADER
    ASSET --> BROW
    LOADER --> BROW
```

---

## 2. Repository structure (simplified)

```mermaid
flowchart TB
    subgraph root["splunk-monitoring-use-cases/"]
        makefile["Makefile<br/>make build"]
        toolsb["tools/build/build.py"]
        content["content/cat-NN-slug/<br/>_category.json, UC-*.json"]
        readme["README.md"]
        diagram["CODEBASE-DIAGRAM.md"]

        subgraph docs["docs/"]
            D0["architecture.md"]
            D1["DESIGN.md"]
            D2["use-case-fields.md"]
        end

        subgraph tools["tools/build/"]
            T1["parse_content.py"]
            T2["render_pages.py"]
            T3["render_api.py"]
            T4["render_search.py"]
            T5["render_meta.py"]
        end

        subgraph distg["dist/ (gitignored output)"]
            dx["api/, browse/, uc/<br/>assets/, exports/"]
        end
    end

    content --> toolsb
    toolsb --> distg
    makefile --> toolsb
```

---

## 3. Build pipeline (v7 data flow)

```mermaid
flowchart LR
    subgraph inputs["Inputs"]
        A["content/cat-*/UC-*.json"]
        B["content/cat-*/_category.json"]
        C["data/ · schemas/<br/>src/ · public/"]
    end

    subgraph pipeline["tools/build/build.py"]
        P1["parse_content"]
        P2["render_assets"]
        P3["render_pages"]
        P4["render_api +<br/>render_search"]
        P5["render_exports"]
        P6["render_meta"]
        P7["integrity + BUILD-INFO"]
    end

    subgraph out["dist/"]
        O1["api/catalog-index.json<br/>api/cat-N.json"]
        O2["browse/, sitemaps,<br/>llms*.txt"]
        O3["assets/app.*.js<br/>search-shard-*.json"]
    end

    A --> P1
    B --> P1
    C --> P1
    P1 --> P2 --> P3 --> P4 --> P5 --> P6 --> P7
    P7 --> O1
    P7 --> O2
    P7 --> O3
```

---

## 4. Use case on disk (v7)

Each canonical use case is **`content/cat-NN-slug/UC-X.Y.Z.json`** validated against `schemas/uc.schema.json`. Optional long-form markdown may sit beside the JSON for prose-heavy UCs.

```mermaid
flowchart TB
    subgraph file["UC-X.Y.Z.json (conceptual)"]
        ID["id, title, criticality,<br/>difficulty, monitoringType"]
        TA["app / TA references,<br/>data sources"]
        SPL["splQuery + CIM /<br/>compliance blocks"]
        META["wave, prerequisites,<br/>MITRE, references, …"]
    end
```

---

## 5. Category groups (dashboard filter)

```mermaid
flowchart LR
    subgraph groups["CAT_GROUPS (catalog-index)"]
        infra["infra<br/>1,2,5,6,15,18,19"]
        security["security<br/>9,10,17"]
        cloud["cloud<br/>3,4,20"]
        app["app<br/>7,8,11,12,13,14,16"]
        industry["industry<br/>21"]
        compliance["compliance<br/>22"]
        business["business<br/>23"]
    end

    subgraph examples["Category examples"]
        E1["Server & Compute"]
        E2["Virtualization"]
        E3["Identity & Access"]
        E4["Containers"]
        E5["Databases"]
        E6["Industry Verticals"]
        E7["Regulatory & Compliance"]
        E8["Business Analytics"]
    end

    infra --> E1
    infra --> E2
    security --> E3
    cloud --> E4
    app --> E5
    industry --> E6
    compliance --> E7
    business --> E8
```

---

## 6. End-to-end flow

```mermaid
sequenceDiagram
    participant Author
    participant JSON as content/cat-*/UC-*.json
    participant Build as tools/build/build.py
    participant Dist as dist/api/*.json
    participant User
    participant SPA as /browse/

    Author->>JSON: Edit UC JSON + category metadata
    Author->>Build: Run make build
    Build->>Dist: Emit catalog-index, cat slices, pages
    User->>SPA: Open site
    SPA->>Dist: GET catalog-index.json
    SPA->>Dist: Lazy GET cat-N.json / v1 APIs
    SPA->>User: Filters, cards, search (7,364+ UCs)
```
