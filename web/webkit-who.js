function get_daily_commits(data){
  return get_daily_commits_filtered(data,null,true);
}

// filters is an array of filter
// Each filter is either:
// - a string -> value = count for that keyword
// - an array of strings -> value = sum of counts for these keywords
function get_daily_commits_filtered(data,filters,add_sum){
  commits = new Array();
  for (var i=0;i<data.length;i++){
      date = new Date(data[i][0]);
      row = [date];
      if(add_sum){
        total_count = data[i][1];
        row.push(total_count);
      }
      if(filters){    
          records = data[i][2];
          for(var j=0;j<filters.length;j++){
              split_count = 0;
              split_filters = [];
              if(typeof filters[j] === 'string'){
                split_filters.push(filters[j]);
              }else{
                split_filters = filters[j];
              }
              for(var k=0;k<split_filters.length;k++){
                split_record = records[split_filters[k]];
                if(split_record){
                    split_count += split_record[0];
                }
              }
              row.push(split_count);
          }
      }
      commits.push(row);
  } 
  return commits;
}

function get_tuple_for_keyword(arr, keyword) {
    for(var i=0; i<arr.length; i++) {
        if (arr[i][0] == keyword){
            return arr[i];
        }
    }
    return null;
}

// Return a sorted array of [keyword,counts] pairs
// representing the total number of hits for each keyword in the dataset
function get_keywords_count(data){
  keywords = [];
  for (var i=0;i<data.length;i++){
    records = data[i][2];
    for (var keyword in records){
        keyword_count = records[keyword][0];
        keyword_tuple = get_tuple_for_keyword(keywords,keyword);
        if (keyword_tuple){
            keyword_tuple[1] += keyword_count;
        }else{
            keywords.push([keyword,keyword_count]);
        }
    }
  }
  // Sort array by counts
  keywords.sort(function(a, b) { return a[1] < b[1] ? 1 : a[1] > b[1] ? -1 : 0 });
  return keywords;
}

function build_graph_from_file(url){
  xhr = new XMLHttpRequest()  
  xhr.onreadystatechange = function()
   { 
     if(xhr.readyState == 4)
     {
        if(xhr.status == 200)
        { 
             data = JSON.parse(xhr.responseText); 
             companies = get_keywords_count(data);
             // Retain only the first 10 contributing companies
             filters = [];
             labels = ['Date'];
             for(var i=0;(i<companies.length && i<10);i++){
                 filters.push(companies[i][0]);
                 labels.push(companies[i][0]);             
             }
             // Aggregate the others
             aggregated = [];
             for(var i=10;i<companies.length;i++){
                 aggregated.push(companies[i][0]);
             }
             filters.push(aggregated);
             labels.push('Other');             
             daily =get_daily_commits_filtered(data,filters,false);             
              g = new Dygraph(
                document.getElementById("graphdiv"),
                daily,
                { labels: labels,
                    rollPeriod: 90,
                showRoller: true 
                }
              );
              dp = document.getElementById("displaybar");
              for(i=1;i<labels.length;i++){
                cb = document.createElement('input');
                cb.id = i-1;
                cb.type = "checkbox";
                cb.addEventListener("click",
                                    function(){
                                        g.setVisibility(this.id,this.checked);
                                    },
                                    false);
                cb.checked = true;
                dp.appendChild(cb);
                lb = document.createElement('label');
                lb.for = i-1;
                lb.innerHTML = ' ' + labels[i];
                dp.appendChild(lb);
              }
        } 
       else 
        { 
           alert("Error: returned status code " + xhr.status + " " + xhr.statusText); 
       } 
    } 
 }; 

 xhr.open("GET", url, true);                
 xhr.send(null); 
}
