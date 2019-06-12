    var el = x => document.getElementById(x);
    var coordinates = el('coordinates');

    mapboxgl.accessToken =
      'pk.eyJ1IjoianBrdW5rbGVyIiwiYSI6ImNqZzB0MjFjNDBiam8ycXFweGlnMThmbG8ifQ.vA1aff3tTCIX_zQsPj0cTg';
    var map = new mapboxgl.Map({
      container: 'map',
      style: 'mapbox://styles/mapbox/streets-v11',
      center: [12.094425000000001, 48.998455500000006],
      zoom: 16,
      attributionControl: false,
    });
    map.addControl(new mapboxgl.AttributionControl(), 'top-left')

    var geocoder = new MapboxGeocoder({
      accessToken: mapboxgl.accessToken,
      marker: {
        color: "red",
        draggable: true,
      },
      mapboxgl: mapboxgl
    });

    document.getElementById('geocoder').appendChild(geocoder.onAdd(map));

    function addBuildings() {
      // Insert the layer beneath any symbol layer.
      var layers = map.getStyle().layers;

      var labelLayerId;
      for (var i = 0; i < layers.length; i++) {
        if (layers[i].type === 'symbol' && layers[i].layout['text-field']) {
          labelLayerId = layers[i].id;
          break;
        }
      }

      map.addLayer({
        'id': '3d-buildings',
        'source': 'composite',
        'source-layer': 'building',
        'filter': ['==', 'extrude', 'true'],
        'type': 'fill-extrusion',
        'minzoom': 15,
        'paint': {
          'fill-extrusion-color': '#aaa',

          // use an 'interpolate' expression to add a smooth transition effect to the
          // buildings as the user zooms in
          'fill-extrusion-height': [
            "interpolate", ["linear"],
            ["zoom"],
            15, 0,
            15.05, ["get", "height"]
          ],
          'fill-extrusion-base': [
            "interpolate", ["linear"],
            ["zoom"],
            15, 0,
            15.05, ["get", "min_height"]
          ],
          'fill-extrusion-opacity': .6
        }
      }, labelLayerId);

      map.setPitch(45);
      map.setBearing(-17.6);
    };

    var layerList = document.getElementById('menu');
    var inputs = layerList.getElementsByTagName('input');

    function switchLayer(layer) {
      var layerId = layer.target.id;
      map.setStyle('mapbox://styles/mapbox/' + layerId);
      map.setPitch(0);
      map.setBearing(0);
    }

    for (var i = 0; i < inputs.length; i++) {
      inputs[i].onclick = switchLayer;
    }


    function analyze() {
      var loc_input = document.getElementById("geocoder").getElementsByTagName("input");
      var img_width = 300;
      var img_height = 500;
      var url =
        'https://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial/lat,lon/17?ms=width,height&od=1&c=de-DE&key=AijbFhynMi9YlUoC5sbBKfrfbnkcMJ34sYBEORQwbsviodnw8nTkkgh5se5COtMs';
      if (loc_input[0].value == "") {
        alert("Bitte geben Sie eine Adresse ein.");
      } else {
        var coords = geocoder.mapMarker.getLngLat();
        new_url = url.replace("lat", coords["lat"])
          .replace("lon", coords["lng"])
          .replace("APIKEY", mapboxgl.accessToken)
          .replace("width", img_width)
          .replace("height", img_height);
      };
      console.log(new_url);

      //el("analyze-button").innerHTML = "Analyzing...";
      var xhr = new XMLHttpRequest();
      var loc = window.location;
      xhr.open("POST", `${loc.protocol}//${loc.hostname}:${loc.port}/analyze`,
        true);
      xhr.onerror = function () {
        alert(xhr.responseText);
      };
      xhr.onload = function (e) {
        if (this.readyState === 4) {
          var response = JSON.parse(e.target.responseText);
          el("address-label").innerHTML = loc_input[0].value;
          el("result-label").innerHTML = `Eingestuft als ${response["result"]}`;
          el("result-probabilities").innerHTML = `Mit folgenden Wahrscheinlichkeiten:`;
          el("probability-verygood").innerHTML = `${response["Sehr_Gut"]}`;
          el("probability-good").innerHTML = `${response["Gut"]}`;
          el("probability-average").innerHTML = `${response["Mittel"]}`;
          el("probability-bad").innerHTML = `${response["Schlecht"]}`;
          el("aerial-image-preview").src = new_url;
          el("aerial-image-link").href = new_url;
          el("details-pane").style.visibility = "visible";
          // alert(`Klassifiziert als ${response["result"]}`);
        }
        // el("analyze-button").innerHTML = "Analyze";
      };

      var fileData = new FormData();
      fileData.append("file", new_url);
      xhr.send(fileData);
    }

    // Animated Submit Button
    const button = document.querySelector(".submit-button"),
      stateMsg = document.querySelector(".pre-state-msg");

    const updateButtonMsg = function () {
      button.classList.add("state-1", "animated");

      setTimeout(finalButtonMsg, 2000);
      el("details-pane").style.visibility = 'hidden';
    };

    const finalButtonMsg = function () {
      button.classList.add("state-2");

      setTimeout(setInitialButtonState, 2000);
      analyze();
    };

    const setInitialButtonState = function () {
      button.classList.remove("state-1", "state-2", "animated");
    };

    button.addEventListener("click", updateButtonMsg);

    // display coordinates after marker was moved
    function onDragEnd() {
      var lngLat = geocoder.mapMarker.getLngLat();
      coordinates.style.display = 'block';
      coordinates.innerHTML = 'Longitude: ' + lngLat.lng + '<br />Latitude: ' + lngLat.lat;
    }

    function addCode() {
      geocoder.mapMarker.on("dragend", onDragEnd);
      onDragEnd();
    }

    // Workaround: we add our event handler to mapMarker only after it is created!
    // mapMarker is only created when a result has been geocoded!
    geocoder.on("result", addCode);