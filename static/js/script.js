// Without jQuery
const onReady = (callback) =>{
  if (document.readyState!='loading') callback();
  else if (document.addEventListener) document.addEventListener('DOMContentLoaded', callback);
  else document.attachEvent('onreadystatechange', function() {
    if (document.readyState=='complete') callback();
  });
};


function generateTableHead(table, data) {
  // https://www.valentinog.com/blog/html-table/
  let thead = table.createTHead();
  let row = thead.insertRow();
  for (let key of data) {
      let th = document.createElement("th");
      let text = document.createTextNode(key);
      th.appendChild(text);
      row.appendChild(th);
  }
}

function generateTable(table, data) {
  for (let element of data) {
    let row = table.insertRow();
    for (key in element) {
      let cell = row.insertCell();
      let text = document.createTextNode(element[key]);
      cell.appendChild(text);
    }
  }
}

function update_stats(stats) {
  document.getElementById('trains').innerHTML = stats[0].journeys
  document.getElementById('delays').innerHTML = stats[0].delays
  console.log('Her er lenke til rådataene')
  console.log(stats[0].api_str)
}

function update_table(interval_value) {
  fetch('/update?' + new URLSearchParams({
    interval: interval_value,
    terminus: document.getElementById('terminus').value,
    line: document.getElementById('line').value,
    display : document.querySelector('input[name="visningsvalg"]:checked').value
}))
  .then((response) => response.json())
  .then((response) => {
    var num_rows = document.querySelector("#test_table").rows.length
    if (num_rows > 0) {
      var table_id = document.getElementById("test_table")
      table_id.deleteTHead();
      table_id.removeChild(table_id.getElementsByTagName("tbody")[0]);
    }
    let table = document.querySelector("#test_table");
    let data = Object.keys(response[0]);
    let table_data = response.slice(0,-1)
    let stats = response.slice(-1)
    update_stats(stats)           
    generateTable(table, table_data);
    generateTableHead(table, data);
  });
}

function fill_line_dropdown() {
  var lines = ['', 'F1', 'F4', 'F5', 'F6', 'F7', 'F8', 'FLY1', 'FLY2', 'L1', 'L2', 'L4', 'L5', 'R12', 'R13', 'R14', 'R21', 'R22', 'R31', 'R40', 'R45', 'R50', 'R60', 'R65', 'R70', 'R71', 'R75', 'RE10', 'RE11', 'RE20', 'RE30']
  var options = "";
  for (const line of lines) {
    options += "<option>"+ line +"</option>";
  }
  document.getElementById("line").innerHTML = options
}

function fill_station_dropdown() {
  var stations = ['', 'Arendal', 'Arna', 'Asker', 'Bergen', 'Bodø', 'Dal', 'Dombås', 'Drammen', 'Egersund', 'Eidsvoll', 'Flåm', 'Gjøvik', 'Göteborg C', 'Halden', 'Hamar', 'Jaren', 'Kongsberg', 'Kongsvinger', 'Lillehammer', 'Lillestrøm', 'Lundamo', 'Melhus', 'Mo i Rana', 'Mosjøen', 'Moss', 'Myrdal', 'Mysen', 'Nelaug', 'Nærbø', 'Oslo Lufthavn', 'Oslo S', 'Røros', 'Ski', 'Skien', 'Spikkestad', 'Stabekk', 'Stavanger', 'Steinkjer', 'Storlien', 'Trondheim S', 'Åndalsnes']
  var options = "";
  for (const station of stations) {
    options += "<option>"+ station +"</option>";
  }
  document.getElementById("terminus").innerHTML = options
}


function run_update() {
  var interval = 30
  update_table(interval)
  var today = new Date();
  document.getElementById('demo').innerHTML = today.toTimeString().split(' ')[0]
}

const timeAroundClock = 58500
const degreePerMinute = 360 / 60
const degreePerHour = 360 / 12
const degreePerHourInMinutes = degreePerHour / 60

onReady(() => { 
  run_update()

  document.querySelector('#updateButton').addEventListener('click', (e) => {
    run_update()
  });

  fill_line_dropdown()
  fill_station_dropdown()



  window.addEventListener('DOMContentLoaded', () => {
      firstMinute()
  })

  document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
          let animations = document.getAnimations()
          if (animations.length > 0) {
              animations.forEach(animation => {
                  animation.finish()
              })
          }
      } else {
          firstMinute()
      }
  })

});


function firstMinute() {
    const dateNow = new Date();
    const elapsed = dateNow.getSeconds() * 1000 + dateNow.getMilliseconds()

    hour(dateNow.getHours(), dateNow.getMinutes())
    setMinute(dateNow.getMinutes())
    if (elapsed >= timeAroundClock) {
        finishedMinuteAnimation()
    } else {
        second(elapsed / timeAroundClock, (timeAroundClock - elapsed) / timeAroundClock)
    }
}

async function finishedMinuteAnimation() {
    const initialHour = new Date().getHours()
    const initialMinute = new Date().getMinutes()
    let newMinute = await nextMinute()
    if (newMinute === 0) {
        newMinute = 60
    }
    second()
    minute(initialMinute, newMinute)
    hour(initialHour, newMinute)
}

function nextMinute() {
    return new Promise(resolve => {
        const now = new Date()
        const remainingMilliseconds = ((60 - now.getSeconds()) * 1000) + (1000 - now.getMilliseconds())
        setTimeout(() => {
            resolve(new Date().getMinutes())
        }, remainingMilliseconds)
    })
}

function hour(hour, minute) {
    const hourInDegree = (hour % 12) * degreePerHour
    const hourElement = document.querySelector('.hours-container');
    hourElement.style.transform = 'rotate(' + (hourInDegree + (minute * degreePerHourInMinutes)) + 'deg)'
    hourElement.style.opacity = 1
}

function setMinute(value) {
    const minuteElement = document.querySelector('.minutes-container');
    minuteElement.style.transform = 'rotate(' + (value * degreePerMinute) + 'deg)'
    minuteElement.style.opacity = 1
}

function minute(initialMinute, newMinute) {
    const minuteElement = document.querySelector('.minutes-container');
    if (newMinute === 60) {
        let animation = minuteElement.animate([
            {transform: 'rotate(' + initialMinute * degreePerMinute + 'deg)'},
            {transform: 'rotate(' + newMinute * degreePerMinute + 'deg)'}
        ], {duration: 300, iterations: 1, easing: 'cubic-bezier(1, 2.52, 0.71, 0.6)', fill: 'forwards'})
        animation.finished.then(() => {
            minuteElement.style.transform = 'rotate(0deg)'
        })
        animation.play()
    } else {
        let animation = minuteElement.animate([
            {transform: 'rotate(' + initialMinute * degreePerMinute + 'deg)'},
            {transform: 'rotate(' + newMinute * degreePerMinute + 'deg)'}
        ], {duration: 300, iterations: 1, easing: 'cubic-bezier(1, 2.52, 0.71, 0.6)', fill: 'both'}).play()
    }
}

function second(start = 0, iterations = 1) {
    const secondsElement = document.querySelector('.seconds-container');
    let animation = secondsElement.animate([
        {transform: 'rotate(0)', easing: 'cubic-bezier(0.2, 0, 1, 1)'},
        {transform: 'rotate(0.25turn)', easing: 'cubic-bezier(0.11, 0.12, 0.85, 0.86)', offset: 0.25},
        {transform: 'rotate(0.95turn)', easing: 'cubic-bezier(1, 1.36, 0.88, 0.88)', offset: 0.95},
        {transform: 'rotate(1turn)'}
    ], {
        duration: timeAroundClock,
        fill: 'none',
        iterationStart: start,
        iterations: iterations
    })
    animation.finished.then(() => {
        finishedMinuteAnimation()
    })
    animation.play()
    secondsElement.style.opacity = 1
}