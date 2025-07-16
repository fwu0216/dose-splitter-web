from flask import Flask, request, render_template_string
from datetime import datetime, timedelta
import math

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>放射性药物分装计算器</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; background: #f7f9fc; max-width: 480px; margin: auto; }
        h1 { color: #007aff; font-size: 24px; text-align: center; }
        .section { background: white; padding: 16px; border-radius: 12px; margin-top: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        label { display: block; margin-top: 10px; font-weight: bold; }
        input, select { padding: 8px; width: 100%; font-size: 16px; border: 1px solid #ccc; border-radius: 8px; box-sizing: border-box; }
        .btn-primary { background-color: #007aff; color: white; font-size: 16px; padding: 10px; border: none; border-radius: 8px; width: 100%; margin-top: 10px; cursor: pointer; }
        .time-buttons { display: flex; justify-content: space-between; margin-top: 10px; gap: 6px; }
        .time-buttons button { flex: 1; padding: 6px 0; font-size: 14px; background-color: #e5f0ff; color: #007aff; border: none; border-radius: 8px; }
        .highlight { color: #007aff; font-weight: bold; font-size: 16px; display: block; margin-top: 8px; text-align: center; }
        .result { margin-top: 10px; font-size: 16px; color: #000; background: #f0f8ff; padding: 10px; border-radius: 8px; white-space: pre-line; }
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

            {% if highlight_volume %}
            <span class="highlight">【{{ highlight_volume }} mL】</span>
            {% endif %}

            <button type="submit" class="btn-primary">计算</button>

            {% if result_text %}
            <div class="result">{{ result_text }}</div>
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

    window.onload = () => {
        fields.forEach(id => {
            const saved = localStorage.getItem(id);
            if (saved !== null) {
                document.getElementById(id).value = saved;
            }
        });
    };

    fields.forEach(id => {
        document.getElementById(id).addEventListener('input', e => {
            localStorage.setItem(id, e.target.value);
        });
    });

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

def decay_activity(initial_activity, elapsed_minutes, half_life):
    return initial_activity * (0.5 ** (elapsed_minutes / half_life))

def calculate_volume(dose, concentration):
    return dose / concentration if concentration else 0

def format_result(header, activity, concentration, volume):
    return f"[{header}]\n当前活度: {activity:.2f} mCi\n当前浓度: {concentration:.3f} mCi/mL\n所需抽取体积: {volume:.3f} mL"

@app.route('/', methods=['GET', 'POST'])
def index():
    activity = request.form.get('activity', '178.8')
    volume = request.form.get('volume', '10')
    dose = request.form.get('dose', '7.9')
    init_time = request.form.get('init_time', '07:40')
    target_time = request.form.get('target_time', '07:50')
    nuclide = request.form.get('nuclide', 'F18')
    result_text = ""
    highlight_volume = ""

    try:
        half_life = 109.7 if nuclide == 'F18' else 20.3
        t0 = datetime.strptime(init_time, "%H:%M")
        t_target = datetime.strptime(target_time, "%H:%M")

        results = []
        for label, offset in [("目标时间 (推荐)", 0), ("提前5分钟", -5), ("延迟5分钟", 5)]:
            t = t_target + timedelta(minutes=offset)
            elapsed = (t - t0).total_seconds() / 60
            cur_act = decay_activity(float(activity), elapsed, half_life)
            conc = cur_act / float(volume)
            vol = calculate_volume(float(dose), conc)
            if label.startswith("目标时间"):
                highlight_volume = f"{vol:.3f}"
            results.append(format_result(label, cur_act, conc, vol))

        result_text = "\n\n".join(results)

    except Exception:
        result_text = ""

    return render_template_string(HTML_TEMPLATE,
                                  activity=activity,
                                  volume=volume,
                                  dose=dose,
                                  init_time=init_time,
                                  target_time=target_time,
                                  nuclide=nuclide,
                                  result_text=result_text,
                                  highlight_volume=highlight_volume)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
