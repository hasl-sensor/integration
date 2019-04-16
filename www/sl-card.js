class SLCard extends HTMLElement {
    set hass(hass) {
        if (!this.content) {
            const card = document.createElement('ha-card');
            this.content = document.createElement('div');     
            card.appendChild(this.content);
            this.appendChild(card);
        }
        
        const config = this.config;
        
        function getEntitiesContent(data) {
            var html =`<style>
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

            ha-icon.alert {
                color: red;
            }

            table.sl-table {
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

            th.col3, td.col3 {
                text-align: right;
                line-height: 18px;
            }

            /* Icons - Default for Boats and Metro Blue Line */
            .line-icon {
                width: auto;                
                border-radius: 2px;                
                background: #0089ca;
                padding: 3px 3px 0 3px;
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

            .line-icon.trm.trm_12 {
                background-color: #778da7;
            }

            .line-icon.trm.trm_21 {
                background-color: #b76020;
            }

            .line-icon.trm.trm_22 {
                background-color: #d77d00;
            }
            </style>`;
            // Add data to table.
            var updatedDate = "";
            if (config.name) html += " <div class=\"header\"><div class=\"name\">" + config.name + "</div></div>"
			
            for (var i = 0; i < data.length; i++){

                const entity_data = hass.states[data[i]]
                if (typeof entity_data === 'undefined'){
                    console.log('Entity data missing')
                }
                else{
					if (!config.name) html +="<div class=\"header\">" + entity_data.attributes.friendly_name + "</div>"					
                    html += "<table class=\"sl-table\">"

                    if (config.departures===true) {
                        if (config.header === true) {    
                            html += `
                               <tr>
                                    <th class="col1">Line</th>
                                    <th class="col2">Destination</th>
                                    <th class="col3">Departure</th>
                                </tr>
                        `
                        }

                        if (typeof entity_data.attributes.departures !== 'undefined') {
                            for (var j = 0; j < entity_data.attributes.departures.length; j++) {
							
							var depTime = '';
							if (config.timeleft===true) {	
								depTime = entity_data.attributes.departures[j].departure
							} else {
								var expectedTime = new Date(entity_data.attributes.departures[j].expected);
								depTime = expectedTime.toLocaleTimeString('sv-SE', { hour: "numeric", 
                                             minute: "numeric"})
							}
                            
                            var lineNumber = entity_data.attributes.departures[j].line;

                            var typeClass = '';

                            switch (entity_data.attributes.departures[j].type) {
                            case 'Buses':
                                typeClass = ' ' + 'bus_red bus_red_' + lineNumber;
                                break;
                            case 'Trams':
                                typeClass = ' ' + 'trm trm_' + lineNumber;
                                break;
                            case 'Metros':
                                switch (lineNumber) {
                                case '10':
                                case '11':
                                    typeClass = ' ' + 'met_blue met_blue_' + lineNumber;;
                                    break;
                                case '13':
                                case '14':
                                    typeClass = ' ' + 'met_red met_red_' + lineNumber;
                                    break;
                                case '17':
                                case '18':
                                case '19':
                                    typeClass = ' ' + 'met_green met_green_' + lineNumber;
                                    break;                                
                                }
                                break;
                            case 'Trains':
                                typeClass = ' ' + 'trn trn_' + lineNumber;
                                break;
                            }

                            var spanClass = 'line-icon' + typeClass;
                                                        
                            html += `
                                <tr>
                                    <td class="col1"><ha-icon icon="${entity_data.attributes.departures[j].icon}"></ha-icon></td>
                                    <td class="col2"><span class="${spanClass}">${lineNumber}</span> ${entity_data.attributes.departures[j].destination}</td>
                                    <td class="col3">${depTime}</td>
                                </tr>
                            `
                            }
                        }
                    }
                    if (config.deviations===true) {    
                        if (typeof entity_data.attributes.deviations !== 'undefined') {
                            for (var k = 0; k < entity_data.attributes.deviations.length; k++) {
                            html += `
                                <tr>
                                    <td class="col1"><ha-icon class="alert" icon="mdi:alert-outline"></ha-icon></td>
                                    <td class="col2" colspan="2"><b>${entity_data.attributes.deviations[k].title}</b><br/><i>${entity_data.attributes.deviations[k].details}</i></td>
                                </tr>
                            `
                            }
                        }
                    } //deviations
                    if (config.updated===true) {    
                        var updatedDate = new Date(entity_data.last_updated);
                        html += `<tr>
                                <td colspan="3" align="left"><sub><i>Last updated ${updatedDate.toLocaleString('sv-SE')}</i></sub></th>
                            </tr>`;
                    }    
                    html += `</table>`;
                    
                }
            }
            return html;
        }
        this.content.innerHTML = getEntitiesContent(this.config.entities);
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

customElements.define('sl-card', SLCard);
