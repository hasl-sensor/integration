const lang = {
    'sv-SE': {        
      entity_missing: 'Ingen data hittades', bus: 'Buss',
      metro: 'Tunnelbana',
      light_railway: 'Lokalbana',
      commuter_train: 'Pendeltåg',
      tram: 'Spårvagn',
      ferry: 'Båt'
    },
    'en-EN': {        
      entity_missing: 'Entity data missing',
      bus: 'Bus',
      metro: 'Subway',
      light_railway: 'Light Railway',
      commuter_train: 'Commuter Train',
      tram: 'Tram',
      ferry: 'Ferry'       
    }
  }
  
  class HASLTl2Card extends HTMLElement {
    set hass(hass) {
      if (!this.content) {
        const card = document.createElement('ha-card');
        this.content = document.createElement('div');
        card.appendChild(this.content);
        this.appendChild(card);
      }
  
      const config = this.config;
          
      function getEntitiesContent(data) {
        var html = `<style>
            ha-card {
              padding: 16px;
            } 
  
            .header {
              font-family: var(--paper-font-headline_-_font-family);
              -webkit-font-smoothing: var(--paper-font-headline_-_-webkit-font-smoothing);
              font-size: var(--paper-font-headline_-_font-size);
              font-weight: var(--paper-font-headline_-_font-weight);
              letter-spacing: var(--paper-font-headline_-_letter-spacing);
              line-height: var(--paper-font-headline_-_line-height);
              text-rendering: var(--paper-font-common-expensive-kerning_-_text-rendering);
              opacity: var(--dark-primary-opacity);
              padding: 4px 0px 12px;
              display: flex;
              justify-content: space-between;
            }
  
            ha-icon {
              transition: color 0.3s ease-in-out, filter 0.3s ease-in-out;
              width: 24px; 
              height: 24px; 
              color: var(--paper-item-icon-color);
            }
  
            ha-icon.good {
              color: green;
            }
  
            ha-icon.planned {
              color: grey;
            }
  
            ha-icon.minor {
              color: orange;
            }
  
            ha-icon.major {
              color: red;
            }
  
            * {
              box-sizing: border-box;
            }
  
             table.sl-traffic-status-table {
                  width: 100%;
                  border-spacing: 0px 8px;
              }
  
              th.col1, td.col1 {
                  text-align: center;
                  width: 24px;
                  height: 30px;
              }
  
              th.col2, td.col2 {
                  padding-left:10px;
                  text-align: left;
                  line-height: 18px;
              }
  
              th.col2{
                font-size: 18px;
                font-weight: 400;
              }
  
              th.col3, td.col3 {
                  text-align: right;
                  line-height: 18px;
              }
  
              .line-icon {
                width: auto;                
                border-radius: 2px;                
                background: #0089ca;
                padding: 3px 3px 0 3px;
                margin-bottom: 3px;
                color: #fff;
                min-width: 22px;
                height: 22px;
                font-weight: 500;
                display: inline-block;
                text-align: center;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
              }
  
              /* Metros */
              .line-icon.met_green {
                  background-color: #179d4d;
              }
  
              /* Buses and Metro Red Line */
              .line-icon.bus_red, .line-icon.met_red {
                  background-color: #d71d24;
              }            
  
              /* Commuter Trains */
              .line-icon.trn {
                  background-color: #ec619f;
              }
  
              /* Trams */
              .line-icon.trm {
                  background-color: #985141;
              }
  
              .line-icon.trm.trm_7 {
                  background-color: #878a83;
              }
  
              .line-icon.trm.trm_variant {
                  background-color: #b76020;
              }
  
              .line-icon.trm.trm_22 {
                  background-color: #d77d00;
              }
  
            </style>
            `;
  
        var culture = "";
        config.language ? culture = config.language : culture = navigator.language || navigator.userLanguage
        if (!lang.hasOwnProperty(culture)) culture = 'sv-SE'
  
        for (var i = 0; i < data.length; i++) {
          const entity_data = hass.states[data[i]]
          if (typeof entity_data === 'undefined') {
            var str = lang[culture].entity_missing
            console.log(str)
          }
          else {
            var updatedTime = new Date(entity_data.last_updated);
            var updated = updatedTime.toLocaleTimeString(culture, {
                hour: "numeric",
                minute: "numeric"
            })
  
            if (config.name) html += "<div class=\"header\"><div class=\"name\">" + config.name + (config.show_time === true ? ' '  + updated : '') + "</div></div>"
  
            html += getTableRow('bus', entity_data.attributes, culture);
            html += getTableRow('metro', entity_data.attributes, culture);
            html += getTableRow('light_railway', entity_data.attributes, culture);
            html += getTableRow('commuter_train', entity_data.attributes, culture);
            html += getTableRow('tram', entity_data.attributes, culture);
            html += getTableRow('ferry', entity_data.attributes, culture);
          }
        }
  
        return html;
      }
  
      this.content.innerHTML = getEntitiesContent(config.entities);
  
      function getTableRow(trafficType, attributes, culture) {
        var status = attributes.metro_status;
        var status_icon = attributes.metro_icon;
        var traffic_type_icon = "mdi:subway-variant";
        var events = attributes.metro_events;
        var iconClass = '';
      
        switch (trafficType) {
          case 'bus':
            status = attributes.bus_status;
            status_icon = attributes.bus_icon;
            events = attributes.bus_events;
            traffic_type_icon = "mdi:bus";
            iconClass = ' bus_red';
            break;
          case 'ferry':
            status = attributes.ferry_status;
            status_icon = attributes.ferry_icon;
            events = attributes.ferry_events;
            traffic_type_icon = "mdi:ferry";
            break;
          case 'tram':
            status = attributes.tram_status;
            status_icon = attributes.tram_icon;
            events = attributes.tram_events;
            traffic_type_icon = "mdi:tram";
            iconClass = ' trm';
            break;
          case 'commuter_train':
            status = attributes.train_status;
            status_icon = attributes.train_icon;
            events = attributes.train_events;
            traffic_type_icon = "mdi:train";
            iconClass = ' trn';
            break;
          case 'light_railway':
            status = attributes.local_status;
            status_icon = attributes.local_icon;
            events = attributes.local_events;
            traffic_type_icon = "mdi:train-variant";
            iconClass = ' trm trm_21';
            break;
        }
      
        var trafficTypeLang = lang[culture][trafficType];
      
        var html = '';
      
        if (status !== 'undefined') {
          html += "<table class=\"sl-traffic-status-table\">"
          html += `
              <tr>
                  <th class="col1"><ha-icon icon="${traffic_type_icon}"></ha-icon></th>
                  <th class="col2">${trafficTypeLang}</th>      
                  <th class="col3"><ha-icon class="${status.toLowerCase()}" icon="${status_icon}"></ha-icon></td>                    
              </tr>
              `
      
          if (events.length > 0 && config.hide_events !== true) {
            for (var j = 0; j < events.length; j++) {
      
              var eventStatusIcon = "mdi:check";
      
              switch (events[j].StatusIcon) {
                case 'EventMajor':
                  eventStatusIcon = "mdi:close";
                  break;
                case 'EventMinor':
                  eventStatusIcon = "mdi:clock-alert-outline"
                  break;
                case 'EventPlanned':
                  eventStatusIcon = "mdi:triangle-outline"
                  break;
              }
      
              switch (events[j].TrafficLine) {
                case 'Spårväg City':
                  iconClass = " trm trm_7";
                  break;
                case 'Tvärbanan':
                  iconClass = " trm trm_22"
                  break;
                case 'Gröna linjen':
                  iconClass = " met_green"
                  break;
                case 'Röda linjen':
                 iconClass = " met_red"
                  break;
              }
              
              var showEvent = true;
  
              if(config.show_only_disturbances === true && events[j].StatusIcon === "EventGood")
              {
                showEvent = false;
              }
  
              if(showEvent)
              {
                html += `<tr>`
                  html += `<td class="col1"></td>`
                  html += `<td class="col2">${events[j].TrafficLine !== null ?
                          `<span class="line-icon${iconClass}"><b>${events[j].TrafficLine}</b></span><br/>` : ''} ${events[j].Message.replace("Övriga linjer:", "<span class=\"line-icon\"><b>Övriga linjer</b></span><br/>").replace("inga större störningar", "Inga större störningar")}</td>` 
                  html += `<td class="col3" valign="top"><ha-icon class="${events[j].StatusIcon.replace("Event", "").toLowerCase()}" icon="${eventStatusIcon}"></ha-icon></td>`  
                html += `</tr>`
              }            
            }
          }
          html += "</table>"
        }
      
        return html;
      }
    }
  
    setConfig(config) {
      if (!config.entities) {
        throw new Error('You need to define one or more entities');
      }
      this.config = config;
    }
  
    // The height of your card. Home Assistant uses this to automatically
    // distribute all cards over the available columns. This kind of works but it is very dynamic
    getCardSize() {
      return this.config.entities.length + 1;
    }
  }
  
  customElements.define('hasl-tl2-card', HASLTl2Card);