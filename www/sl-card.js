class SLCard extends HTMLElement {
    set hass(hass) {
        if (!this.content) {
            const card = document.createElement('ha-card');
            card.header = this.config.name;
            this.content = document.createElement('div');
            this.content.style.padding = '0 16px 16px';
            card.appendChild(this.content);
            this.appendChild(card);
        }
        
        function getEntitiesContent(data) {
            var html = `
            <table width="100%">
                <tr>
                    <th align="left">Linje</th>
                    <th align="left">Slutstation</th>
                    <th align="left">Avgång</th>
                </tr>
            `;
            // Add data to table.
            var updatedDate = "";
            for (var i = 0; i < data.length; i++){
                const entity_data = hass.states[data[i]]
                if (typeof entity_data === 'undefined'){
                    console.log('Entity data missing')
                }
                else{
                    if (typeof entity_data.attributes.departure_board !== 'undefined') {
                        for (var j = 0; j < entity_data.attributes.departure_board.length; j++) {
                        html += `
                            <tr>
                                <td align="left"><ha-icon style="width: 20px; height: 20px;" icon="${entity_data.attributes.departure_board[j].icon}"></ha-icon> ${entity_data.attributes.departure_board[j].line}</td>
                                <td align="left">${entity_data.attributes.departure_board[j].destination}</td>
                                <td align="left">${entity_data.attributes.departure_board[j].departure}</td>
                            </tr>
                        `}
                    }
                    if (typeof entity_data.attributes.deviances !== 'undefined') {
                        for (var k = 0; k < entity_data.attributes.deviances.length; k++) {
                        html += `
                            <tr>
                                <td align="left" colspan="3">&nbsp;</td>
                            </tr>
                            <tr>
                                <td align="left" colspan="3"><ha-icon style="width: 20px; height: 20px;" icon="mdi:alert-outline"></ha-icon> <b>${entity_data.attributes.deviances[k].title}</b></td>
                            </tr>
                            <tr>
                                <td align="left" colspan="3"><i>${entity_data.attributes.deviances[k].details}</i></td>
                            </tr>
                        `}
                    }
                    
                }
                var updatedDate = new Date(entity_data.last_updated);
            }
            html += `
            <table width="100%">
                <tr colspan=3>
                    <td align="left"><sub><i>Senast uppdaterat: ${updatedDate.toLocaleTimeString()}</i></sub></th>
                </tr>
            `;
            // Close table.
            html += `</table>`;
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
