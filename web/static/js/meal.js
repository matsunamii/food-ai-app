// AI検出結果を保存
let detectedFoods = [];

// 料理入力フォーム追加
function addFood(value = "") {

  const container = document.getElementById("food-list");

  const div = document.createElement("div");
  div.className = "input-group mb-2 position-relative";

  const input = document.createElement("input");
  input.type = "text";
  input.name = "foods[]";
  input.className = "form-control";
  input.placeholder = "料理名";
  input.value = value;

  // 手入力変更時も再計算
  input.addEventListener("input", updateNutrition);

  const suggest = document.createElement("div");
  suggest.className = "suggestions";

  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "btn btn-outline-danger";
  btn.textContent = "削除";

  btn.onclick = () => {
    div.remove();
    updateNutrition();
  };

  div.appendChild(input);
  div.appendChild(suggest);
  div.appendChild(btn);

  container.appendChild(div);
  setupAutocomplete(input);
}

// 入力フォーム初期化
function clearFoodListKeepOne() {

  const container = document.getElementById("food-list");

  const items = container.querySelectorAll(".input-group");

  items.forEach((el, idx) => {

    if (idx === 0) {

      el.querySelector('input[name="foods[]"]').value = "";

    } else {

      el.remove();

    }

  });

}

// 栄養再計算
function updateNutrition(){

  const inputs = document.querySelectorAll('input[name="foods[]"]');

  let totalCal = 0;
  let totalProtein = 0;
  let totalFat = 0;
  let totalCarb = 0;

  inputs.forEach(i => {

    const name = i.value.trim();

    if(!name) return;

    const food = foodByName[name];

    if(food){

      totalCal += Number(food.cal) || 0;
      totalProtein += Number(food.protein) || 0;
      totalFat += Number(food.fat) || 0;
      totalCarb += Number(food.carb) || 0;

    }

  });

  document.querySelector('input[name="calorie"]').value = totalCal;
  document.querySelector('input[name="protein"]').value = totalProtein;
  document.querySelector('input[name="fat"]').value = totalFat;
  document.querySelector('input[name="carb"]').value = totalCarb;

}

// AI解析
document.getElementById("autoFillBtn").addEventListener("click", async () => {

  const fileInput = document.getElementById("fileUpload");
  const status = document.getElementById("aiStatus");

  const img = document.getElementById("previewImage");

  if (!fileInput.files || fileInput.files.length === 0) {

    status.textContent = "画像を選択してください。";
    return;

  }

  status.textContent = "解析中…";

  const fd = new FormData();
  fd.append("img", fileInput.files[0]);

  try {

    const res = await fetch("/classify", {
      method: "POST",
      body: fd
    });

    const data = await res.json();

    if (!data.ok) {

      status.textContent = "失敗: " + (data.error || "unknown");
      return;

    }

    // AI検出結果保存
    detectedFoods = data.foods || [];

    const foods = detectedFoods;

    img.onload = () => {
      drawBoxes(img, foods);
    };

    img.src = URL.createObjectURL(fileInput.files[0]);
    img.style.display = "block";

    const names = foods.map(x => x.food101).filter(Boolean);

    const uniq = [...new Set(names)];

    clearFoodListKeepOne();

    if (uniq.length === 0) {

      status.textContent = "食べ物を検出できませんでした。";
      return;

    }

    /* 料理名入力 */

    const first = document.querySelector('#food-list input[name="foods[]"]');

    if (first) {

      first.value = uniq[0];
      first.addEventListener("input", updateNutrition);

    } else {

      addFood(uniq[0]);

    }

    for (let i = 1; i < uniq.length; i++) {

      addFood(uniq[i]);

    }

    /* 栄養計算 */

    updateNutrition();

    status.textContent = `入力しました（${uniq.length}件）`;

  } catch (e) {

    console.error(e);
    status.textContent = "通信エラー/サーバーエラーが発生しました。";

  }

});

function drawBoxes(image, detections){

  const canvas = document.getElementById("bboxCanvas");
  const ctx = canvas.getContext("2d");

  const imgWidth = image.clientWidth;
  const imgHeight = image.clientHeight;

  canvas.width = imgWidth;
  canvas.height = imgHeight;

  const scaleX = imgWidth / 640;
  const scaleY = imgHeight / 640;

  ctx.clearRect(0,0,canvas.width,canvas.height);

  detections.forEach(det => {

    const [x1,y1,x2,y2] = det.bbox;

    const x = x1 * scaleX;
    const y = y1 * scaleY;
    const w = (x2-x1) * scaleX;
    const h = (y2-y1) * scaleY;

    ctx.strokeStyle = "red";
    ctx.lineWidth = 3;
    ctx.strokeRect(x,y,w,h);

    ctx.fillStyle = "red";
    ctx.font = "16px Arial";
    ctx.fillText(det.food101,x,y-5);

  });

}

function setupAutocomplete(input){

  const box = input.parentElement.querySelector(".suggestions");

  input.addEventListener("input", () => {

    const word = input.value.trim();

    box.innerHTML = "";

    if(!word) return;

    const foods = Object.keys(foodByName)
      .filter(name => name.includes(word))
      .slice(0,5);

    foods.forEach(f => {

      const div = document.createElement("div");
      div.className = "suggestion-item";
      div.textContent = f;

      div.onclick = () => {

        input.value = f;
        box.innerHTML = "";
        updateNutrition();

      };

      box.appendChild(div);

    });

  });

}
document.querySelectorAll(".food-input").forEach(setupAutocomplete);