erDiagram
    USERS ||--o{ CLUB_MEMBERSHIPS : has
    USERS ||--o{ MEMBER_TRANSACTIONS : has
    CLUBS ||--o{ CLUB_MEMBERSHIPS : has
    CLUBS ||--o{ FUNDS : has
    CLUBS ||--o{ UNIT_VALUE_HISTORIES : has
    CLUBS ||--o{ MEMBER_TRANSACTIONS : has
    CLUBS ||--o{ FUND_SPLITS : has

    CLUB_MEMBERSHIPS }o--|| USERS : belongs_to
    CLUB_MEMBERSHIPS }o--|| CLUBS : belongs_to

    FUNDS ||--o{ POSITIONS : has
    FUNDS ||--o{ TRANSACTIONS : has
    FUNDS }o--|| CLUBS : belongs_to
    FUNDS ||--o{ FUND_SPLITS : has_split_for

    FUND_SPLITS }o--|| CLUBS : belongs_to_club
    FUND_SPLITS }o--|| FUNDS : applies_to_fund

    ASSETS ||--o{ POSITIONS : held_as
    ASSETS ||--o{ TRANSACTIONS : involved_in
    ASSETS ||--o{ ASSETS : underlies (for options)

    POSITIONS }o--|| FUNDS : belongs_to
    POSITIONS }o--|| ASSETS : is_of

    TRANSACTIONS }o--|| FUNDS : belongs_to
    TRANSACTIONS }o--o| ASSETS : relates_to (optional)
    TRANSACTIONS }o--o| TRANSACTIONS : reverses (optional)
    TRANSACTIONS }o--o| TRANSACTIONS : related_to (optional)

    UNIT_VALUE_HISTORIES }o--|| CLUBS : belongs_to

    MEMBER_TRANSACTIONS }o--|| USERS : belongs_to
    MEMBER_TRANSACTIONS }o--|| CLUBS : belongs_to

    USERS {
        UUID id PK
        String auth0_sub UK, Index
        String email UK, Index
        Boolean is_active
        DateTime created_at
        DateTime updated_at
    }
    CLUBS {
        UUID id PK
        String name Index
        String description
        Numeric bank_account_balance
        DateTime created_at
        DateTime updated_at
    }
    CLUB_MEMBERSHIPS {
        UUID id PK
        UUID user_id FK
        UUID club_id FK
        ClubRole role
        DateTime created_at
        DateTime updated_at
        UniqueConstraint(user_id, club_id)
    }
    FUNDS {
        UUID id PK
        UUID club_id FK
        String name
        String description
        Boolean is_active
        Numeric brokerage_cash_balance
        DateTime created_at
        DateTime updated_at
    }
    FUND_SPLITS {
        UUID id PK
        UUID club_id FK
        UUID fund_id FK
        Numeric split_percentage
        DateTime created_at
        DateTime updated_at
        UniqueConstraint(club_id, fund_id)
    }
    ASSETS {
        UUID id PK
        AssetType asset_type Index
        String symbol Index
        String name
        String(3) currency
        OptionType option_type (nullable)
        Numeric strike_price (nullable)
        Date expiration_date (nullable)
        UUID underlying_asset_id FK (nullable)
        DateTime created_at
        DateTime updated_at
    }
    POSITIONS {
        UUID id PK
        UUID fund_id FK
        UUID asset_id FK
        Numeric quantity
        Numeric average_cost_basis
        DateTime created_at
        DateTime updated_at
        UniqueConstraint(fund_id, asset_id)
    }
    TRANSACTIONS {
        UUID id PK
        UUID fund_id FK
        UUID asset_id FK (nullable)
        TransactionType transaction_type Index
        DateTime transaction_date Index
        Numeric quantity (nullable)
        Numeric price_per_unit (nullable)
        Numeric total_amount (nullable)
        Numeric fees_commissions (nullable)
        Text description (nullable)
        UUID related_transaction_id FK (nullable)
        UUID reverses_transaction_id FK (nullable) Index
        DateTime created_at
        DateTime updated_at
    }
    UNIT_VALUE_HISTORIES {
        UUID id PK
        UUID club_id FK
        Date valuation_date Index
        Numeric total_club_value
        Numeric total_units_outstanding
        Numeric unit_value
        DateTime created_at
        DateTime updated_at
        UniqueConstraint(club_id, valuation_date)
    }
    MEMBER_TRANSACTIONS {
        UUID id PK
        UUID user_id FK
        UUID club_id FK
        MemberTransactionType transaction_type
        DateTime transaction_date Index
        Numeric amount
        Numeric unit_value_used
        Numeric units_transacted
        DateTime created_at
        DateTime updated_at
    }