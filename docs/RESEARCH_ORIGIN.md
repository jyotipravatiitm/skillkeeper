# Research origin and technical lineage

Skillkeeper was inspired by the following paper:

> Siyuan Huang, Pengyu Cheng, Haotian Liu, Tao Chen, Yihao Liu, Jingwei Ni, Shijie Zhou, Ziyi Yang, Gangwei Jiang, Mengyu Zhou, Yu Cheng, Xiaoxi Jiang, and Guanjun Jiang. **Skill Self-Play: Pushing the Frontier of LLM Capability with Co-Evolving Skills.** arXiv:2607.22529, 2026.

**[Read the authoritative PDF on arXiv](https://arxiv.org/pdf/2607.22529v1)** · [Abstract and version history](https://arxiv.org/abs/2607.22529v1) · [Authors' reference implementation](https://github.com/Qwen-Applications/skill-self-play)

The PDF is linked from its authoritative arXiv location rather than copied into this repository. Its arXiv submission uses the non-exclusive distribution license, which grants arXiv permission to distribute it but does not grant this project a general redistribution license.

## The technical idea

Skill Self-Play (Skill-SP) addresses a training problem: fixed environments provide reliable verification but limited task variety, while open-ended generation provides variety but can introduce unreliable feedback. The paper combines:

1. A **proposer** that generates challenging tasks from selected skills.
2. A **solver** that attempts those tasks near its current capability frontier.
3. A **dynamic skill controller** that uses execution feedback to refine, add, route, or prune skills.
4. **Verification and reinforcement learning** that jointly improve the task curriculum and model during training.

The paper reports results for tool-call prediction and logical reasoning. Those are results of the authors' training framework; they are not claims about Skillkeeper.

## How Skillkeeper adapts it

Skillkeeper applies the feedback-loop insight to a user-owned skill inventory without requiring model training or a GPU cluster.

| Skill-SP concept | Skillkeeper adaptation |
|---|---|
| Proposer creates frontier tasks | A real failure or correction becomes a replay case |
| Solver attempts generated tasks | The user's existing agent and model execute the skill |
| Verifiers judge validity and utility | Deterministic replay requirements and, later, artifact or trace verifiers provide evidence |
| Skill controller evolves the library | Inventory, health checks, staged candidates, promotion gates, and pruning signals manage skills |
| Co-evolution updates training | Repeated use creates an observe, repair, evaluate, promote, and rollback operating loop |

The safest operational interpretation is not “let an agent rewrite itself.” It is:

```text
observe a failure
    -> turn it into a repeatable check
    -> create an isolated candidate
    -> compare baseline and candidate
    -> test held-out behavior
    -> let a human promote explicitly
    -> preserve the previous version for rollback
```

## Boundary

Skillkeeper is **inspired by** Skill-SP; it is not an official companion project, an implementation of the paper's reinforcement-learning system, or a reproduction of its benchmark results.

The current release implements local inventory, explicit replay checks, candidate staging, promotion gates, tamper checks, audit events, and rollback. Runtime trace ingestion, behavioral graders, artifact-aware verification, autonomous skill induction, and learned routing are roadmap work.

## Citation

If the research idea is useful in your work, cite the original authors:

```bibtex
@article{huang2026skill,
  title   = {Skill Self-Play: Pushing the Frontier of LLM Capability with Co-Evolving Skills},
  author  = {Huang, Siyuan and Cheng, Pengyu and Liu, Haotian and Chen, Tao and Liu, Yihao and Ni, Jingwei and Zhou, Shijie and Yang, Ziyi and Jiang, Gangwei and Zhou, Mengyu and Cheng, Yu and Jiang, Xiaoxi and Jiang, Guanjun},
  journal = {arXiv preprint arXiv:2607.22529},
  year    = {2026},
  url     = {https://arxiv.org/abs/2607.22529}
}
```
