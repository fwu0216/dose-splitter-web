from flask import Flask, request, render_template_string
import math
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>放射性药物分装计算器</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; background: #f7f9fc; }
        h1 { color: #007aff; font-size: 24px; }
        label { display: block; margin-top: 12px; }
        input, select { padding: 8px; width: 100%; font-size: 16px; margin-top: 4px; border: 1px solid #ccc; border-radius: 8px; }
        .section { background: white; padding: 16px; border-radius: 12px; margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.04); }
        .label-inline { display: inline-block; margin-right: 10px; font-weight: bold; color: #333; }
        .row { display: flex; gap: 10px; align-items: center; }
        .result { font-size: 18px; color: #007aff; font-weight: bold; margin-top: 10px; }
        button { margin-top: 16px; padding: 10px 16px; font-size: 16px; background-color: #007aff; color: white; border: none; border-radius: 8px; cursor: pointer; }
        .row-btn { display: flex; align-items: center; gap: 10px; }
        .btn-group { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 8px; }
        .btn-group button { flex: 1; padding: 8px; font-size: 14px; }
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
            <h3 style="color:#007aff; border-left: 4px solid #007aff; padding-left: 6px;">目标设置</h3>
            <label>目标剂量 (mCi):
                <div class="row-btn">
                    <input type="number" step="0.01" name="dose" id="dose" value="{{ dose }}">
                    <button type="submit">开始计算</button>
                </div>
            </label>

            <label>目标分装时间:
                <input type="time" name="target_time" id="target_time" value="{{ target_time }}">
            </label>

            <div class="btn-group">
                <button type="button" onclick="addMinutes(5)">+5min</button>
                <button type="button" onclick="addMinutes(10)">+10min</button>
                <button type="button" onclick="addMinutes(15)">+15min</button>
                <button type="button" onclick="addMinutes(20)">+20min</button>
            </div>

            {% if result_volume %}
                <div class="result">目标所需体积：{{ result_volume }} mL</div>
            {% endif %}
        </div>

        <div class="section">
            <h3 style="color:#007aff; border-left: 4px solid #007aff; padding-left: 6px;">初始信息</h3>
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

    // 恢复本地保存的数据
    window.onload = () => {
        fields.forEach(id => {
            const saved = localStorage.getItem(id);
            if (saved !== null) {
                document.getElementById(id).value = saved;
            }
        });
    };

    // 监听并保存到 localStorage
    fields.forEach(id => {
        document.getElementById(id).addEventListener('input', e => {
            localStorage.setItem(id, e.target.value);
        });
    });

    // 增加目标分装时间按钮功能
    function addMinutes(mins) {
        const timeInput = document.getElementById("target_time");
        let [hours, minutes] = timeInput.value.split(":").map(Number);
        let total = hours * 60 + minutes + mins;
        total = total % (24 * 60); // 防止超过 24 小时
        const newHours = String(Math.floor(total / 60)).padStart(2, '0');
        const newMinutes = String(total % 60).padStart(2, '0');
        const newTime = `${newHours}:${newMinutes}`;
        timeInput.value = newTime;
        localStorage.setItem('target_time', newTime);
    }
</script>
</body>
</html>
'''

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

    try:
        half_life = 109.7 if nuclide == 'F18' else 20.3
        t1 = datetime.strptime(init_time, "%H:%M")
        t2 = datetime.strptime(target_time, "%H:%M")
        elapsed = (t2 - t1).total_seconds() / 60
        current_activity = decay_activity(float(activity), elapsed, half_life)
        concentration = current_activity / float(volume)
        result_volume = round(calculate_volume(float(dose), concentration), 3)
    except Exception:
        result_volume = None

    return render_template_string(HTML_TEMPLATE,
                                  activity=activity,
                                  volume=volume,
                                  dose=dose,
                                  init_time=init_time,
                                  target_time=target_time,
                                  nuclide=nuclide,
                                  result_volume=result_volume)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

#if __name__ == '__main__':
 #   import os
  #  port = int(os.environ.get('PORT', 10000))
   # app.run(host='0.0.0.0', port=port, debug=False)
