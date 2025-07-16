from flask import Flask, request, render_template_string
import math
from datetime import datetime, timedelta

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>放射性药物分装计算器</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            padding: 12px;
            margin: 0;
            background: #f7f9fc;
        }
        h1 {
            color: #007aff;
            font-size: 20px;
            text-align: center;
        }
        .section {
            background: white;
            padding: 16px;
            border-radius: 12px;
            margin-top: 16px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        }
        label {
            font-weight: bold;
            color: #333;
            margin-top: 8px;
            display: block;
        }
        input, select {
            padding: 8px;
            width: 100%;
            font-size: 16px;
            margin-top: 4px;
            border: 1px solid #ccc;
            border-radius: 8px;
            box-sizing: border-box;
        }
        button {
            padding: 10px;
            font-size: 16px;
            background-color: #007aff;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            width: 100%;
            margin-top: 10px;
        }
        .time-buttons {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 6px;
            margin: 10px 0;
        }
        .time-buttons button {
            background-color: #e5f0ff;
            color: #007aff;
            flex: 1;
            padding: 8px;
        }
        .result-box {
            background: #eaf4ff;
            padding: 12px;
            margin-top: 12px;
            border-radius: 8px;
            font-size: 14px;
        }
        .highlight {
            color: #0057d9;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>放射性药物分装计算器</h1>
    <form method="post">
        <div class="section">
            <label>选择核素:
                <select name="nuclide" id="nuclide">
                    <option value="F18" {% if nuclide == 'F18' %}selected{% endif %}>F18</option>
                    <option value="C11" {% if nuclide == 'C11' %}selected{% endif %}>C11</option>
                </select>
            </label>
        </div>

        <div class="section">
            <label>目标剂量 (mCi):
                <input type="number" step="0.01" name="dose" id="dose" value="{{ dose }}">
            </label>

            <label>目标分装时间:
                <input type="time" name="target_time" id="target_time" value="{{ target_time }}">
            </label>

            <div class="time-buttons">
                <button type="button" onclick="addMinutes(5)">+5min</button>
                <button type="button" onclick="addMinutes(10)">+10min</button>
                <button type="button" onclick="addMinutes(15)">+15min</button>
                <button type="button" onclick="addMinutes(20)">+20min</button>
            </div>

            {% if result_volume %}
                <div class="highlight" style="text-align:center;">[{{ result_volume }} mL]</div>
            {% endif %}
            <button type="submit">计算</button>

            {% if result_info %}
                <div class="result-box">
                    {{ result_info|safe }}
                </div>
            {% endif %}
        </div>

        <div class="section">
            <label>初始活度 (mCi):
                <input type="number" step="0.1" name="activity" id="activity" value="{{ activity }}">
            </label>
            <label>初始体积 (mL):
                <input type="number" step="0.1" name="volume" id="volume" value="{{ volume }}">
            </label>
            <label>初始时间:
                <input type="time" name="init_time" id="init_time" value="{{ init_time }}">
            </label>
        </div>
    </form>

<script>
    const fields = ['nuclide', 'activity', 'volume', 'init_time', 'dose', 'target_time'];

    // 恢复本地存储
    window.onload = () => {
        fields.forEach(id => {
            const saved = localStorage.getItem(id);
            if (saved !== null) {
                document.getElementById(id).value = saved;
            }
        });
    };

    // 保存用户输入
    fields.forEach(id => {
        document.getElementById(id).addEventListener('input', e => {
            localStorage.setItem(id, e.target.value);
        });
    });

    // 增加时间按钮
    function addMinutes(mins) {
        const timeInput = document.getElementById("target_time");
        if (!timeInput.value) return;
        const [hh, mm] = timeInput.value.split(":").map(Number);
        const date = new Date();
        date.setHours(hh, mm + mins);
        const newTime = date.toTimeString().slice(0,5);
        timeInput.value = newTime;
        localStorage.setItem("target_time", newTime);
    }
</script>
</body>
</html>
'''

# 计算函数
def decay_activity(initial_activity, elapsed_minutes, half_life):
    return initial_activity * (0.5 ** (elapsed_minutes / half_life))

def calculate_volume(dose, concentration):
    return dose / concentration if concentration else 0

@app.route('/', methods=['GET', 'POST'])
def index():
    activity = request.form.get('activity', '178.8')
    volume = request.form.get('volume', '10')
    dose = request.form.get('dose', '7.9')
    init_time = request.form.get('init_time', '07:40')
    target_time = request.form.get('target_time', '07:50')
    nuclide = request.form.get('nuclide', 'F18')
    result_volume = None
    result_info = ""

    try:
        half_life = 109.7 if nuclide == 'F18' else 20.3
        t0 = datetime.strptime(init_time, "%H:%M")
        vt = datetime.strptime(target_time, "%H:%M")
        dose = float(dose)
        act = float(activity)
        vol = float(volume)

        def generate_info(label, offset):
            t = vt + timedelta(minutes=offset)
            mins = (t - t0).total_seconds() / 60
            curr_act = decay_activity(act, mins, half_life)
            conc = curr_act / vol if vol else 0
            vol_needed = calculate_volume(dose, conc)
            return f'''
<b>[{label}]</b><br>
当前活度: {curr_act:.2f} mCi<br>
当前浓度: {conc:.3f} mCi/mL<br>
所需抽取体积: {vol_needed:.3f} mL<br>
'''

        result_info += generate_info("目标时间（推荐）", 0)
        result_info += generate_info("提前5分钟", -5)
        result_info += generate_info("延迟5分钟", 5)

        elapsed = (vt - t0).total_seconds() / 60
        current_activity = decay_activity(act, elapsed, half_life)
        concentration = current_activity / vol
        result_volume = round(calculate_volume(dose, concentration), 3)

    except Exception:
        result_volume = None

    return render_template_string(HTML_TEMPLATE,
                                  activity=activity,
                                  volume=volume,
                                  dose=dose,
                                  init_time=init_time,
                                  target_time=target_time,
                                  nuclide=nuclide,
                                  result_volume=result_volume,
                                  result_info=result_info)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
