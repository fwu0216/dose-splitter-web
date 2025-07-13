from flask import Flask, request, render_template_string
from datetime import datetime, timedelta

app = Flask(__name__)

HALF_LIFE_DICT = {
    'F18': 109.7,
    'C11': 20.3
}

def decay_activity(initial_activity, elapsed_minutes, half_life):
    return initial_activity * (0.5 ** (elapsed_minutes / half_life))

def calculate_concentration(activity, volume):
    return activity / volume if volume else 0

def calculate_volume(dose, concentration):
    return dose / concentration if concentration else 0

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>放射性药物分装计算器</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial;
            background-color: #f2f2f7;
            margin: 0;
            padding: 16px;
        }
        .container {
            max-width: 600px;
            margin: auto;
        }
        h2 {
            text-align: center;
            color: #007aff;
            margin-bottom: 20px;
        }
        .card {
            background-color: #fff;
            padding: 16px;
            border-radius: 14px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        .section-title {
            font-size: 16px;
            font-weight: bold;
            color: #007aff;
            margin-bottom: 12px;
            border-left: 4px solid #007aff;
            padding-left: 10px;
        }
        label {
            display: block;
            margin-top: 10px;
            color: #333;
            font-weight: 500;
            font-size: 15px;
        }
        input, select {
            width: 100%%;
            padding: 10px;
            font-size: 16px;
            border-radius: 10px;
            border: 1px solid #ccc;
            box-sizing: border-box;
            margin-top: 5px;
        }
        input[type="submit"] {
            background-color: #007aff;
            color: white;
            font-weight: bold;
            border: none;
            padding: 10px;
            width: 100%%;
        }
        .result-box {
            background: #eef6ff;
            border-left: 4px solid #007aff;
            padding: 16px;
            border-radius: 10px;
            font-size: 15px;
            white-space: pre-wrap;
        }
        .inline-value {
            margin-top: 12px;
            text-align: right;
            color: #007aff;
            font-weight: bold;
            font-size: 16px;
        }
        .flex-row {
            display: flex;
            gap: 8px;
        }
        .flex-row > div {
            flex: 1;
        }
        .flex-row .button-cell {
            flex: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>放射性药物分装计算器</h2>
        <form method="post">
            <div class="card">
                <label>选择核素:</label>
                <select name="nuclide">
                    <option value="F18" {% if nuclide == "F18" %}selected{% endif %}>F18</option>
                    <option value="C11" {% if nuclide == "C11" %}selected{% endif %}>C11</option>
                </select>
            </div>

            <div class="card">
                <div class="section-title">目标设置</div>
                <div class="flex-row">
                    <div>
                        <label>目标剂量 (mCi):</label>
                        <input type="text" name="dose" value="{{ dose }}">
                    </div>
                    <div class="button-cell" style="align-self: flex-end;">
                        <label style="visibility: hidden;">开始计算</label>
                        <input type="submit" value="开始计算">
                    </div>
                </div>

                <label>目标分装时间:</label>
                <input type="time" name="target_time" value="{{ target_time }}">

                {% if volume_main %}
                <div class="inline-value">目标所需体积：{{ volume_main }} mL</div>
                {% endif %}
            </div>

            <div class="card">
                <div class="section-title">初始信息</div>
                <label>初始活度 (mCi):</label>
                <input type="text" name="init_activity" value="{{ init_activity }}">

                <label>初始体积 (mL):</label>
                <input type="text" name="init_volume" value="{{ init_volume }}">

                <label>初始时间:</label>
                <input type="time" name="start_time" value="{{ start_time }}">
            </div>
        </form>

        {% if result %}
        <div class="card result-box">
            <strong>计算结果：</strong><br><br>
            {{ result }}
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    init_activity = "178.8"
    init_volume = "10"
    dose = "7.56"
    start_time = "07:40"
    target_time = "07:50"
    nuclide = "F18"
    result = ""
    volume_main = None

    if request.method == 'POST':
        try:
            nuclide = request.form['nuclide']
            init_activity = request.form['init_activity']
            init_volume = request.form['init_volume']
            dose = request.form['dose']
            start_time = request.form['start_time']
            target_time = request.form['target_time']

            half_life = HALF_LIFE_DICT[nuclide]
            start_dt = datetime.strptime(start_time, "%H:%M")
            target_dt = datetime.strptime(target_time, "%H:%M")

            def make_result(title, shift_min):
                t_shift = target_dt + timedelta(minutes=shift_min)
                elapsed = (t_shift - start_dt).total_seconds() / 60
                act = decay_activity(float(init_activity), elapsed, half_life)
                conc = calculate_concentration(act, float(init_volume))
                vol = calculate_volume(float(dose), conc)
                return f"[{title}]\n当前活度: {act:.2f} mCi\n当前浓度: {conc:.3f} mCi/mL\n所需抽取体积: {vol:.3f} mL\n", vol

            txt_main, volume_main = make_result("目标时间(推荐)", 0)
            txt_early, _ = make_result("提前5分钟", -5)
            txt_late, _ = make_result("延迟5分钟", 5)

            result = f"{txt_main}\n{txt_early}\n{txt_late}"
            volume_main = f"{volume_main:.3f}"

        except Exception as e:
            result = f"错误: {e}"

    return render_template_string(HTML_TEMPLATE,
                                  init_activity=init_activity,
                                  init_volume=init_volume,
                                  dose=dose,
                                  start_time=start_time,
                                  target_time=target_time,
                                  nuclide=nuclide,
                                  result=result,
                                  volume_main=volume_main)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
