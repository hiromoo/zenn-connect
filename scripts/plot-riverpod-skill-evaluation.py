"""Generate the article chart with matplotlib (Python 3.10+).

Data: hiromoo/flutter-riverpod-skill, commit fd01483,
benchmarks/iteration-{1,2,3,8,9}.md. Iterations 8/9 use three-run totals.
Run: MPLCONFIGDIR=/tmp/riverpod-mpl python3 scripts/plot-riverpod-skill-evaluation.py
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

ROOT = Path(__file__).resolve().parents[1]
font = FontProperties(fname='/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc')
plt.rcParams.update({'font.family': font.get_name(), 'font.size': 14})
labels = ['Iteration 1\n各条件1回', 'Iteration 2\n各条件1回', 'Iteration 3\n各条件1回', 'Iteration 8\n各条件3回の合計', 'Iteration 9\n各条件3回の合計']
functional = [(6, 7), (6, 7), (4, 7), (20, 21), (21, 21)]
conventions = [(3, 11), (9, 11), (11, 11), (31, 33), (33, 33)]
fig, axes = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
fig.patch.set_facecolor('#ffffff')
fig.suptitle('Skillありの評価結果：規約の適合と機能要件は別に見る', fontsize=19, y=.975)
for ax, title, values, color in zip(axes, ['機能要件', 'Skillの規約'], [functional, conventions], ['#1876A3', '#C46526']):
    ax.set_title(title, loc='left', fontsize=17, pad=12, color=color)
    rates = [a / b * 100 for a, b in values]
    ax.barh(range(5), rates, height=.57, color=color)
    ax.set_yticks(range(5), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 116)
    ax.set_xticks([0, 25, 50, 75, 100], ['0%', '25%', '50%', '75%', '100%'])
    ax.set_axisbelow(True)
    ax.grid(axis='x', color='#DEE4EA', linewidth=.8)
    ax.tick_params(axis='both', length=0, pad=10, labelbottom=True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for i, ((a, b), rate) in enumerate(zip(values, rates)):
        ax.text(rate + 1.6, i, f'{a}/{b}', va='center', fontsize=14, color='#273444')
fig.text(.05, .052, '各回で既存アプリの3ケースを評価。Iteration 8・9は同じSkill版の3回分を集計。', fontsize=11, color='#526070')
fig.text(.05, .027, 'CLI・検証条件の変更があるため、差をSkillの変更だけの効果とは解釈できない。', fontsize=11, color='#526070')
fig.subplots_adjust(left=.23, right=.95, top=.90, bottom=.11, hspace=.38)
fig.savefig(ROOT / 'images/riverpod-skill-evaluation-progress.png', dpi=180, facecolor='white')
plt.close(fig)

# Exact solver totals from local iteration-9-run{1,2,3}/benchmark.json.
# Only aggregate measurements are retained here; no transcripts or config.
seconds_without = [825.084, 374.248, 786.102]
seconds_with = [1001.766, 732.722, 1179.462]
tokens_without = [1424484, 822662, 805928]
tokens_with = [4570192, 1741194, 3258773]
fig, axes = plt.subplots(2, 1, figsize=(10, 9))
fig.patch.set_facecolor('white')
fig.suptitle('Iteration 9：実装時間と計測トークン数', fontsize=20, y=.97)
colors = ['#738596', '#1876A3']
for ax, title, baseline, assisted, unit, limit, ticks in [
    (axes[0], '実装時間', [s / 60 for s in seconds_without], [s / 60 for s in seconds_with], '分', 24, [0, 5, 10, 15, 20]),
    (axes[1], '計測トークン数', [t / 10000 for t in tokens_without], [t / 10000 for t in tokens_with], '万', 540, [0, 100, 200, 300, 400, 500]),
]:
    ratio = sum(assisted) / sum(baseline)
    total = f'{sum(baseline):.1f} → {sum(assisted):.1f}{unit}'
    ax.set_title(f'{title}  ｜  3回合計 {total}（約{ratio:.1f}倍）', loc='left', fontsize=16, pad=14)
    for offset, values, color, label in [(-.18, baseline, colors[0], 'Skillなし'), (.18, assisted, colors[1], 'Skillあり')]:
        positions = [i + offset for i in range(3)]
        ax.barh(positions, values, height=.30, color=color, label=label)
        for y, value in zip(positions, values):
            ax.text(value + limit * .015, y, f'{value:.1f}{unit}', va='center', fontsize=13, color='#273444')
    ax.set_yticks(range(3), ['1回目', '2回目', '3回目'])
    ax.invert_yaxis()
    ax.set_xlim(0, limit)
    ax.set_xticks(ticks, [f'{t}{unit}' for t in ticks])
    ax.set_axisbelow(True)
    ax.grid(axis='x', color='#DEE4EA', linewidth=.8)
    ax.tick_params(axis='both', length=0, pad=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
fig.legend(*axes[0].get_legend_handles_labels(), loc='upper center', bbox_to_anchor=(.5, .932), ncol=2, frameon=False, fontsize=14)
fig.text(.05, .065, '各回・各条件の3ケースを合算。実装モデルの時間・トークンのみ（採点は含まない）。', fontsize=11, color='#526070')
fig.text(.05, .035, 'トークン数はキャッシュされた入力を含む。課金額や、その倍率を示す数値ではない。', fontsize=11, color='#526070')
fig.subplots_adjust(left=.14, right=.96, top=.83, bottom=.15, hspace=.55)
fig.savefig(ROOT / 'images/riverpod-skill-evaluation-cost.png', dpi=180, facecolor='white')
plt.close(fig)
