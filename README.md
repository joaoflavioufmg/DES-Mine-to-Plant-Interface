## Supplementary Material – SBPO 2025

This supplementary material accompanies the article titled **"Integrated Analysis of the Mine-to-Plant Interface Using Discrete Event Simulation"**, submitted to **SBPO 2025**.

The paper presents an integrated analysis of the **supply chain of a Brazilian mining company**, with a specific focus on the **mine-to-plant interface**, where **discrete flows** (trucks) interact with **continuous flows** (crushing processes). 

![Figure 1](https://github.com/joaoflavioufmg/DES-Mine-to-Plant-Interface/blob/main/figs/interface.png "Mine-to-Plant Interface")

### Summary of the Study

The main contribution of this work lies in the **combination of an analytical method** with **Discrete Event Simulation (DES)** to:

- Investigate **variability propagation** throughout the system.
- Propose **operational changes** that improve overall performance.
- Test solutions **safely** in a virtual environment before implementation.

- ![Figure 2](https://github.com/joaoflavioufmg/DES-Mine-to-Plant-Interface/blob/main/figs/pit.png "Open pit and Mine-to-Plant operations")


- The system Activity Cycle Diagram is presented below:

![Figure 3](https://github.com/joaoflavioufmg/DES-Mine-to-Plant-Interface/blob/main/figs/DCA.png "ACD of the Mine-to-Plant Interface operations")

Three scenarios were analyzed:

- **Scenario A**: Implementation of a **safety stock** between the mine and the plant.
- **Scenario B**: **Increase in the number of trucks** in operation (from 26 to 30).
- **Scenario C**: **50% reduction in micro-stoppages** in the crushing process.

### Key Findings

- **Productivity gains of up to 6.5%** were observed.
- Simple operational changes—like reducing micro-stoppages—can lead to **significant improvements** without the need for major investments.
- DES was essential in identifying **true bottlenecks** and evaluating proposed solutions in a **controlled and replicable** manner.
- The approach enhances system **stability**, **robustness**, and **profitability**.

### Files Included

To support reproducibility and testing, the following **simulation files** are attached:

1. `current_situation.py` – Calibrated base model reflecting the existing system.
2. `A_scenario_safety_stock.py` – Simulation of Scenario A (Safety Stock).
3. `B_scenario_more_trucks.py` – Simulation of Scenario B (Additional Trucks).
4. `C_scenario_fewer_microstoppages.py` – Simulation of Scenario C (Reduced Micro-Stoppages).

These files are intended for educational and research purposes and can be used to test and validate the findings discussed in the paper.
---
For questions or additional information, please contact the corresponding author.

## Current Situation

With the current situation accurately **simulated and calibrated** to reflect operational reality, it serves as the baseline for comparing alternative scenarios.

### Simulation Configuration

- **Statistical confidence level:** 95%
- **Number of replications:** 16
- **Duration of each replication:** 180 days
- **Warm-up period:** 5 days
- **System behavior:** All statistics and variables were reset at the beginning of each replication.

### Operational Conditions

The simulation considered the mine’s **existing resource conditions**:

- **Loaders:** 14 allocated for mine loading, plus 1 assigned to the intermediate stockpile.
- **Trucks:** 26 trucks transporting material on a daily basis.
- **Crushing lines:** Two primary crushing lines, each fed by a **550 m³ capacity** silo.

This baseline scenario provides the foundation for evaluating the impact of proposed improvements or adjustments in subsequent simulations.

## Simulation Scenarios

### Scenario A: Implementation of Safety Stock

To simulate **Scenario A**, the creation of a safety stock between the mine and the plant was considered. The necessary volume for this stock was calculated based on historical data, taking into account:

- The **longest stoppage time** at the mine during the 13 months observed.
- The **mine’s processing capacity** during that period.

The **ideal safety stock** was established at **123.58 kt**.

Operational behavior in this scenario:

- When the **mine is operating**, it supplies the silos and replenishes the safety stock if its level has dropped.
- If a **stoppage occurs at the mine**, trucks are redirected to load from the safety stock until normal operations resume.
- One of the mine’s **loaders was relocated** to the safety stock to facilitate this flow.
- All other parameters remained **constant**.
---

### Scenario B: Increased Truck Availability

In **Scenario B**, all operational parameters remained **unchanged** compared to the current scenario, **except for the number of trucks**:

- Instead of the usual **26 trucks**, the simulation considered **all 30 trucks** owned by the plant.
- The objective was to evaluate system performance with **maximum truck availability**.
---

### Scenario C: Reduction in Micro-Stoppages

For **Scenario C**, all parameters were **maintained**, but a change was introduced in the **crushing process stoppage behavior**:

- A **50% reduction in micro-stoppages** was considered.
- This adjustment altered the **distribution of stoppage times**, potentially improving overall efficiency in the crushing stage.
---
