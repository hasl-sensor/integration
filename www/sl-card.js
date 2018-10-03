class SLCard extends HTMLElement {
    set hass(hass) {
        if (!this.content) {
            const card = document.createElement('ha-card');
            card.header = 'SL Card';
            this.content = document.createElement('div');
            this.content.style.padding = '0 16px 16px';
            card.appendChild(this.content);
            this.appendChild(card);
        }
        function getEntitiesContent(data) {
            var html = `
            <table width="100%">
                <tr>
                    <th align="left">Stop</th>
                    <th align="left">Line</th>
                    <th align="left">Destination</th>
                    <th align="left">Departure</th>
                </tr>
            `;
            // Add data to table.
            for (var i = 0; i < data.length; i++){
                const entity_data = hass.states[data[i]]
                if (typeof entity_data === 'undefined'){
                    console.log('Entity data missing')
                }
                else{
                    html += `
                        <tr>
                            <td align="left">${entity_data.attributes.friendly_name}</td>
                            <td align="left">${entity_data.attributes.next_line}</td>
                            <td align="left">${entity_data.attributes.next_destination}</td>
                            <td align="left">${entity_data.attributes.next_departure}</td>
                        </tr>
                        <tr>
                            <td align="left">${entity_data.attributes.friendly_name}</td>
                            <td align="left">${entity_data.attributes.upcoming_line}</td>
                            <td align="left">${entity_data.attributes.upcoming_destination}</td>
                            <td align="left">${entity_data.attributes.upcoming_departure}</td>
                        </tr>
                    `
                }
            }
            // Close table.
            html += `</table>`;
            return html;
        }
        this.content.innerHTML = getEntitiesContent(this.config.entities)
        console.log(this.content.innerHTML)
    }

    setConfig(config) {
        if (!config.entities) {
            throw new Error('You need to define one or more entities');
        }
    this.config = config;
    }

    // The height of your card. Home Assistant uses this to automatically
    // distribute all cards over the available columns.
    getCardSize() {
        return this.config.entities.length + 1;
    }
}

customElements.define('sl-card', SLCard);
