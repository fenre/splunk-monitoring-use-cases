# Splunk Monitoring Use Cases — Codebase Diagram

This document visualizes the repository structure, build pipeline, and data flow.

---

## 1. High-level architecture

```mermaid
flowchart LR
    subgraph sources["Source (Markdown)"]
        INDEX["INDEX.md\ncategory metadata\nicons, starters"]
        CAT["cat-01 … cat-20\nuse case content\nSPL, CIM, TAs"]
    end

    subgraph build["Build"]
        PY["build.py\nparse & emit JS"]
    end

    subgraph output["Output"]
        DATA["data.js\nDATA, CAT_META\nCAT_GROUPS, EQUIPMENT"]
    end

    subgraph app["App"]
        HTML["index.html\ndashboard UI"]
        CUSTOM["custom-text.js\nsite text overrides"]
    end

    INDEX --> PY
    CAT --> PY
    PY --> DATA
    DATA --> HTML
    CUSTOM --> HTML
```

---

## 2. Repository structure

```mermaid
flowchart TB
    subgraph root["splunk-monitoring-use-cases/"]
        build["build.py"]
        validate["validate_md.py"]
        data["data.js (generated)"]
        catalog["catalog.json (generated)"]
        index["index.html"]
        custom["custom-text.js"]
        readme["README.md"]
        diagram["CODEBASE-DIAGRAM.md"]

        subgraph usecases["use-cases/"]
            preamble["cat-00-preamble.md"]
            index_md["INDEX.md"]
            cat1["cat-01-server-compute.md"]
            cat2["cat-02-virtualization.md"]
            catN["… cat-03 … cat-20"]
        end

        subgraph docs["docs/"]
            D1["use-case-fields.md"]
            D2["implementation-guide.md"]
            D3["cim-and-data-models.md"]
            D4["equipment-table.md"]
            D5["category-files-and-names.md"]
            D6["github-pages-setup.md"]
            D7["splunk-apps-use-cases-comparison.md"]
        end
    end

    usecases --> build
    build --> data
    build --> catalog
    data --> index
    custom --> index
```

---

## 3. Build pipeline (data flow)

```mermaid
flowchart LR
    subgraph inputs["Inputs"]
        A["cat-*.md\n(20 files)"]
        B["INDEX.md"]
    end

    subgraph build_steps["build.py"]
        P1["Parse headings\nUC-x.y.z, ## 1.1 …"]
        P2["Parse fields\nCriticality, SPL, CIM…"]
        P3["Parse INDEX.md\nicons, descriptions\nquick starters"]
        P4["Auto-tag equipment\nfrom App/TA patterns"]
        P5["Emit data.js\n+ catalog.json"]
    end

    subgraph js["data.js"]
        D["DATA\ncategories → subs → UCs"]
        M["CAT_META\nicon, description per cat"]
        G["CAT_GROUPS\ninfra, security, cloud, app"]
        E["EQUIPMENT\nvendor → model mapping"]
    end

    A --> P1
    B --> P3
    P1 --> P2
    P2 --> P4
    P4 --> P5
    P3 --> P5
    P5 --> D
    P5 --> M
    P5 --> G
    P5 --> E
```

---

## 4. Use case document structure

Each `cat-XX-*.md` file follows this structure; `build.py` extracts the bolded fields and SPL blocks.

```mermaid
flowchart TB
    subgraph file["cat-XX-*.md"]
        H1["# N. Category Name"]
        H2["## N.1 Subcategory"]
        UC["### UC-N.1.K · Use Case Title"]
        F1["**Criticality** critical/high/medium/low"]
        F2["**Difficulty** beginner/intermediate/advanced/expert"]
        F3["**Monitoring type** Performance/Availability/…"]
        F4["**Value** (why it matters)"]
        F5["**App/TA** (Splunk add-on)"]
        F6["**Data Sources** (index, sourcetype)"]
        F7["**SPL** (code block)"]
        F8["**CIM Models** (or N/A)"]
        F9["**CIM SPL** (optional code block)"]
        F10["**Implementation**"]
        F11["**Visualization**"]
        F12["**Equipment Models** (optional)"]
    end

    H1 --> H2
    H2 --> UC
    UC --> F1
    F1 --> F2
    F2 --> F3
    F3 --> F4
    F4 --> F5
    F5 --> F6
    F6 --> F7
    F7 --> F8
    F8 --> F9
    F9 --> F10
    F10 --> F11
    F11 --> F12
```

---

## 5. Category groups (dashboard filter)

```mermaid
flowchart LR
    subgraph groups["CAT_GROUPS (build.py)"]
        infra["infra\n1,2,5,6,15,18,19"]
        security["security\n9,10,17"]
        cloud["cloud\n3,4,20"]
        app["app\n7,8,11,12,13,14,16"]
    end

    subgraph examples["Category examples"]
        E1["Server & Compute"]
        E2["Virtualization"]
        E3["Identity & Access"]
        E4["Containers"]
        E5["Databases"]
    end

    infra --> E1
    infra --> E2
    security --> E3
    cloud --> E4
    app --> E5
```

---

## 6. End-to-end flow

```mermaid
sequenceDiagram
    participant Author
    participant MD as use-cases/*.md
    participant Build as build.py
    participant JS as data.js
    participant User
    participant HTML as index.html

    Author->>MD: Edit use cases & INDEX.md
    Author->>Build: Run python3 build.py
    Build->>Build: Parse markdown, INDEX, auto-tag equipment
    Build->>JS: Write DATA, CAT_META, CAT_GROUPS, EQUIPMENT
    User->>HTML: Open in browser
    HTML->>JS: Load script
    JS->>HTML: Expose globals
    HTML->>User: Render filters, cards, search
```

---

*Generated for the Splunk Infrastructure Monitoring Use Case Repository.*
