function get_daily_commits(data){
  return get_daily_commits_filtered(data,null,true);
}

function get_daily_commits_for_keyword(data,keyword){
  commits = new Array();
  for (var i=0;i<data.length;i++){
      date = data[i][0];
      nb = data[i][1];
      records = data[i][2];
      if(records[keyword]){
        commits.push([date,nb,records[keyword][1]]);
      }
  } 
  return commits;
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
                    if (split_record instanceof Array){        
                        split_count += split_record[0];
                    } else {
                        split_count += split_record;
                    }
                }
              }
              row.push(split_count);
          }
      }
      commits.push(row);
  } 
  return commits;
}

function get_tuple_for_tag(tags, tag) {
    for(var i=0; i<tags.length; i++) {
        if (tags[i][0] == tag){
            return tags[i];
        }
    }
    return null;
}

// Return a sorted array of [tag,counts,subtags] entries representing
// all level-one tags identified in the dataset.
// For each tag, we store:
// - its name,
// - the total number of hits
// - the list of subtags (and their hits number)
function get_tags_count(data){
  var tags = [];
  for (var i=0;i<data.length;i++){
    var records = data[i][2];
    for (var tag in records){
        var record = records[tag];
        var tag_count;
        if (record instanceof Array){
            tag_count = records[tag][0];
        } else {
            tag_count = records[tag];
        }
        var tag_tuple = get_tuple_for_tag(tags,tag);
        if (tag_tuple){
            tag_tuple[1] += tag_count;
        }else{
            var i = tags.push([tag,tag_count,[]]);
            tag_tuple = tags[i-1];
        }
        if (record instanceof Array){        
            for (var subtag in records[tag][1]){
                subtag_count = records[tag][1][subtag][0];
                subtag_tuple = get_tuple_for_tag(tag_tuple[2],subtag);
                if (subtag_tuple){
                    subtag_tuple[1] += subtag_count;
                }else{
                    tag_tuple[2].push([subtag,subtag_count]);
                }
            }
        }
    }
  }
  // Sort array by counts
  tags.sort(function(a, b) { return a[1] < b[1] ? 1 : a[1] > b[1] ? -1 : 0 });
  return tags;
}

function create_graph_node(container) {
    // Get graph div (we _need_ to have it styled from the markup if
    // we don't want dygraph to select the default width/height
    var graphDiv = document.createElement("div");
    var width = window.getComputedStyle(container).width;
    graphDiv.style.width = width;
    var targetHeight = Math.floor(width.substring(0, width.length - 2)*.6);
    var maxHeight = Math.floor(window.innerHeight*.6);
    graphDiv.style.height = Math.min(targetHeight,maxHeight)+'px';
    container.appendChild(graphDiv);
    return graphDiv;
}

function build_graph_from_data(container,data,nbseries){
    // Create graph node
    var graphDiv = create_graph_node(container);
    // Count keywords
    keywords = get_tags_count(data);
    // Retain the first nbseries contributing keywords as individual filters
    filters = [];
    labels = ['Date'];
    for(var i=0;(i<keywords.length && i<nbseries);i++){
     filters.push(keywords[i][0]);
     labels.push(keywords[i][0]);
    }
    // Aggregate the other keywords into a single filter
    aggregated = [];
    for(var i=nbseries;i<keywords.length;i++){
     aggregated.push(keywords[i][0]);
    }
    filters.push(aggregated);
    labels.push('Other');
    // Get daily commits filtered             
    daily =get_daily_commits_filtered(data,filters,false);             
    g = new Dygraph(
    graphDiv,
    daily,
    { labels: labels,
        rollPeriod: 90,
    showRoller: true 
    }
    );
    // Create display bar to filter out sequences
    var dp = document.createElement("p");
    dp.innerHTML = "Display:";
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
    container.appendChild(dp);
}

// Build a webkit commit graph
// container: containing DOM element
// from: year (>2001)
// to: year
// filter: feature/company
function build_graph(container,from,to,filter){

    data = [];
    year = from;

    fetch_next_dataset = function(){
      xhr = new XMLHttpRequest()  
      xhr.onreadystatechange = function()
       { 
         if(xhr.readyState == 4)
         {
            if(xhr.status == 200)
            { 
                 dataset = JSON.parse(xhr.responseText);
                 data = data.concat(dataset);
                 year++;
                 if(year<=to){
                     fetch_next_dataset();
                 }else{
                    var evt = document.createEvent("Event");
                    evt.initEvent("datarefreshed",true,true); 
                    evt.data = data;
                    container.dispatchEvent(evt);
                 }
            } 
           else 
            { 
               alert("Error: returned status code " + xhr.status + " " + xhr.statusText); 
           } 
        } 
     }; 

     xhr.open("GET", './' + year + '-by-' + filter + '.json', true);                
     xhr.send(null); 
    }
    
    fetch_next_dataset();
}

function onDataRefreshed (evt) {
    build_graph_from_data(container,data,10);
} 

function init(){
    var container = document.getElementById("container");
    if(container){
        // Create inputs to select time range
        var tr = document.createElement("p");
        tr.appendChild(document.createTextNode("WebKit Commits between "));
        var from = document.createElement("input");
        from.type = "number";
        from.min = 2001;
        from.max = new Date().getFullYear();
        from.step = 1;
        from.value = from.max -1;
        tr.appendChild(from);
        tr.appendChild(document.createTextNode(" and "));
        var to = document.createElement("input");
        to.type = "number";
        to.min = 2001;
        to.max = from.max;
        to.step = 1;
        to.value = to.max;
        tr.appendChild(to);
        tr.appendChild(document.createTextNode(" split by "));
        var select = document.createElement("select");
        var filters = ['keyword','company'];
        for(var filter in filters){
            var option = document.createElement("option");
            option.appendChild(document.createTextNode(filters[filter]));
            select.appendChild(option);
        }
        tr.appendChild(select);
        var bt = document.createElement("input");
        bt.type = "submit";
        bt.value = "Refresh";
        bt.onclick = function(){
            for(var i=0;i<2;i++) container.removeChild(tr.nextSibling);
            build_graph(container,from.value,to.value,select.value);            
        };
        tr.appendChild(bt);
        container.appendChild(tr);
        build_graph(container,from.value,to.value,select.value);
    }
    container.addEventListener('datarefreshed',onDataRefreshed,false);
}

function GetFloatValueOfAttr (element,attr) {
    var floatValue = null;
    if (window.getComputedStyle) {
        var compStyle = window.getComputedStyle (element, null);
        try {
            var value = compStyle.getPropertyCSSValue (attr);
            var valueType = value.primitiveType;
            switch (valueType) {
              case CSSPrimitiveValue.CSS_NUMBER:
                  floatValue = value.getFloatValue (CSSPrimitiveValue.CSS_NUMBER);
                  break;
              case CSSPrimitiveValue.CSS_PERCENTAGE:
                  floatValue = value.getFloatValue (CSSPrimitiveValue.CSS_PERCENTAGE);
                  break;
              default:
                  if (CSSPrimitiveValue.CSS_EMS <= valueType && valueType <= CSSPrimitiveValue.CSS_DIMENSION) {
                      floatValue = value.getFloatValue (CSSPrimitiveValue.CSS_PX);
                  }
            }
        } 
        catch (e) {
          // Opera doesn't support the getPropertyCSSValue method
          stringValue = compStyle[attr];
          floatValue = stringValue.substring(0, stringValue.length - 2);
        }
    }
    return floatValue;
}

window.addEventListener("load",init,false);

