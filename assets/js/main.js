window.spotTheBot = {
    domain: "",
    init: function(domain) {
        this.domain = domain;
    },
    openDialog: function(event) {
        document.getElementById('fileid').click();
    },
    logout: function(event) {
        localStorage.removeItem('name_hash');
        window.location.reload();
    },
    onLoaded: function(event) {
        console.log('loaded');
        let contents = event.target.result;
        let lines = contents.split('\n');
        if (lines.length >= 2) {
            let secondLine = lines[1].trim();
            spotTheBot.hashAndStore(secondLine);
            window.location.reload();
        } else {
            console.log("The file does not have a second line.");
        }
    },
    onUpload: function(event) {
       console.log('uploading');
       let file = document.getElementById('fileid').files[0];
       let reader = new FileReader();
       reader.onload = spotTheBot.onLoaded;
       reader.readAsText(file);
    },
    hashAndStore: async function(data) {
        const encoder = new TextEncoder();
        const dataEncoded = encoder.encode(data);
        const hashBuffer = await crypto.subtle.digest('SHA-256', dataEncoded);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        localStorage.setItem('name_hash', hashHex);
        console.log(`Hashed second line: ${hashHex}`);
    },
    shareInvitation: function(event) {
        if (navigator.share) {
            console.log('share supported');
            navigator.share({
                title: 'Spot The Bot!',
                text: 'Mensch oder Maschine?',
                url: this.domain
            }).then(() => {
                console.log('Thanks for sharing!');
            }).catch((error) => {
                console.log('Error sharing:', error);
            });
        } else {
            console.log('share not supported');
        }
    }
};