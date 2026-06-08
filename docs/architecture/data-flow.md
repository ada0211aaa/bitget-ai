# Data Flow

First-version signal flow:

```text
Bitget Agent Hub skills
-> news / macro / technical / sentiment / market intelligence notes
-> hard risk filters
-> signal scoring
-> five-view output
-> Bitget Playbook prompt
-> Playbook backtest / publish record
-> GitHub showcase and devlog materials
```

The first version records outputs manually in documentation files. It does not create a database or background process.
