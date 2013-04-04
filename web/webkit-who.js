// container: containing DOM element
function WWGraph (container,nbseries) {

    // Local variable used to store our data
    var data = null;
    
    // Current graph
    var g = null;
    
    // Series for current graph
    var currentSeries = null;
    
    // Filters applied on current graph
    var currentFilters = null;
    
    /* WWGraph Methods */
    var get_daily_commits_for_keyword = function (data,keyword){
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
    var get_daily_commits_filtered = function (data,filters,add_sum){
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

    var get_tuple_for_tag = function (tags, tag) {
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
    var get_tags_count = function (data){
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

    // Create graph node
    var create_graph_node = function (container) {
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

    this.build_graph_from_data = function (data){
        container.innerHTML ="";
        var graphDiv = create_graph_node(container);
        // Count keywords
        keywords = get_tags_count(data);
        // Retain the first nbseries contributing keywords as individual filters
        filters = [];
        currentSeries = ['Date'];
        for(var i=0;(i<keywords.length && i<nbseries);i++){
         filters.push(keywords[i][0]);
         currentSeries.push(keywords[i][0]);
        }
        // Aggregate the other keywords into a single filter
        aggregated = [];
        for(var i=nbseries;i<keywords.length;i++){
         aggregated.push(keywords[i][0]);
        }
        filters.push(aggregated);
        currentSeries.push('Other');
        // Get daily commits filtered             
        daily = get_daily_commits_filtered(data,filters,false);             
        g = new Dygraph(
            graphDiv,
            daily,
            {   labels: currentSeries,
                rollPeriod: 90,
                showRoller: true 
            }
        );
        var evt = document.createEvent("Event");
        evt.initEvent("graphrefreshed",true,true); 
        evt.series = currentSeries;
        evt.filters = currentFilters;
        container.dispatchEvent(evt);
    }

    // Refresh WebKit commit data
    // The commit data is fetched from network using XHR
    // from: year (>2001)
    // to: year
    // first-level filter: 'keyword'/'company'
    this.refreshData = function (from,to,filter){

        self = this;
        data = [];
        currentFilters = null;

        year = Math.max(2001,from);

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
                        self.build_graph_from_data(data);
                     }
                } 
               else 
                { 
                   container.innerHTML = "<p>Unable to fetch commits data</p>" +
                    "<p>XHR status code: " + xhr.status + " " + xhr.statusText + "</p>"; 
               } 
            } 
         }; 

         xhr.open("GET", './' + year + '-by-' + filter + '.json', true);                
         xhr.send(null); 
        }
        
        fetch_next_dataset();
    }
    
    this.setFilters = function (newfilters) {
        var filtered = data;
        currentFilters = newfilters;
        if (currentFilters && currentFilters[0]) {
            filtered = get_daily_commits_for_keyword(filtered,currentFilters[0]);
            if (currentFilters[1]) {
                filtered = get_daily_commits_for_keyword(filtered,currentFilters[1]);
            }
        }
        this.build_graph_from_data(filtered);
    }
    
    this.setVisibility = function ( index, visible ) {
        g.setVisibility(index,visible);
    }
    
}
