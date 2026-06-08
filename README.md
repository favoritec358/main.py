# Crawling Daily Survey & Poll News of the Cross-Strait Issue

## Introduction

The script aim to scrape on web and obtain the daily news of the latest survey or poll on the cross-strait issue automatically.

## Programming Schedule

- The program executes via the scheduling tool ``Cron``.
- The scheduling time: every **UTC+8** ``4 a.m.`` ``7 a.m.`` ``12 p.m.``

## Diagram

```mermaid
flowchart TD

A(("Search Engine"))
B["Pew"]
C["Gallup"]
D["NCCU ESC"]
E@{ shape: procs, label: "other sources"}
F@{ shape: curv-trap, label: "Email" }
G@{ shape: docs, label: "Receivers"}

subgraph "News Links"
B
C
D
E
end

A--Crawing-->B
A--Crawing-->C
A--Crawing-->D
A--Crawing-->E

B--"Output"-->F
C--"Output"-->F
D--"Output"-->F
E--"Output"-->F
F--"Send"-->G

```
