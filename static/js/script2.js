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
  document.getElementById('api_str').innerHTML = stats[0].api_str
  console.log(stats[0].api_str)
}

function update_table(interval_value) {
  fetch('/update?' + new URLSearchParams({
    interval: interval_value,
    terminus: document.getElementById('terminus').value,
    line: document.getElementById('line').value
}))
  .then((response) => response.json())
  .then((response) => {
    //console.log(response)
    // interval=60&line=R70&terminus=STK'
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


onReady(() => { 

  document.querySelector('#updateButton').addEventListener('click', (e) => {
    console.log('Dette er en test')
    var interval = 30
    if (!(document.getElementById('interval').value=='')) {
      interval = document.getElementById('interval').value
    }
    update_table(interval)
    var today = new Date();
    document.getElementById('demo').innerHTML = today.toTimeString().split(' ')[0]
  });

});