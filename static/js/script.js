
$(document).ready(function(){

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

    function update_table(interval_value) {
        $.ajax({
            url: '/update',
            type: 'get',
            data: {
              interval: interval_value,
              line: $('#line').val()
            },
            success: function(res){
                var num_rows = document.querySelector("#test_table").rows.length
                if (num_rows > 0) {
                    $("#test_table thead").remove(); 
                    $("#test_table tbody").remove(); 
                }
                response = JSON.parse(res)
                let table = document.querySelector("#test_table");
                let data = Object.keys(response[0]);
                let table_data = response.slice(0,-1)
                let stats = response.slice(-1)
                update_stats(stats)           
                generateTable(table, table_data);
                generateTableHead(table, data);
            }
        }) 
    }

    function update_stats(stats) {
        document.getElementById('trains').innerHTML = stats[0].journeys
        document.getElementById('delays').innerHTML = stats[0].delays
        document.getElementById('api_str').innerHTML = stats[0].api_str
        console.log(stats[0].api_str)
    }

    $('#updateButton').click(function(){
        console.log('Dette er en test')
        var interval = 30
        if (!($('#interval').val()=='')) {
          interval = $('#interval').val()
        }
        update_table(interval)
        var today = new Date();
        var time = today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
        document.getElementById('demo').innerHTML = time
    })


    $(function(){
  
        setInterval( function() {
          var hours = new Date().getHours();
          var mins = new Date().getMinutes();
          var hdegree = hours * 30 + (mins / 2);
          var hrotate = "rotate(" + hdegree + "deg)";
          
          $(".hand").css("opacity","1");
          
          $("#hour").css({
            "-webkit-transform" : hrotate,
            "-moz-transform" : hrotate,
            "-ms-transform" : hrotate,
            "-o-transform" : hrotate,
            "transform" : hrotate
          });
          
        }, 1000 );
            
        setInterval( function() {
          var mins = new Date().getMinutes();
          var mdegree = mins * 6;
          var mrotate = "rotate(" + mdegree + "deg)";
          
          $("#minute").css({
            "-webkit-transform" : mrotate,
            "-moz-transform" : mrotate,
            "-ms-transform" : mrotate,
            "-o-transform" : mrotate,
            "transform" : mrotate
          });
          
        }, 1000 );
        
      });

})


//var dt = new Date();
    //document.getElementById('date-time').innerHTML=dt;

    /*
    function displayValue() {
        // gjør get request til main.py 
        document.getElementById("answer").innerHTML = 'hei fra js'
    }
    document.getElementById('updateButton').addEventListener("click", displayValue);
    */

    /*
    let mountains = [
        { name: "Monte Falco", height: 1658, place: "Parco Foreste Casentinesi" },
        { name: "Monte Falterona", height: 1654, place: "Parco Foreste Casentinesi" },
        { name: "Poggio Scali", height: 1520, place: "Parco Foreste Casentinesi" },
        { name: "Pratomagno", height: 1592, place: "Parco Foreste Casentinesi" },
        { name: "Monte Amiata", height: 1738, place: "Siena" }
      ];
      */