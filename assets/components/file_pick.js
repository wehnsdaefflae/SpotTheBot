export default {
    template: `
        <q-file
            v-model="file"
            @update:modelValue="file_pick"
            :label="label"
            :multiple="multiple"
            :accept="accept"
        />
    `,

    props: {
        label: String,
        multiple: Boolean,
        accept: String,
        url: String,
        delete_url: String,  // New prop to accept the backend delete endpoint URL
    },

    setup(props) {  // Added the 'props' parameter to access component properties within setup
        const file = Vue.ref(null);

        // Watch for changes in the file
        Vue.watch(file, async (newVal, oldVal) => {
            if (oldVal && !newVal) {  // If the old value existed and the new value doesn't, a file was removed
                try {
                    const response = await fetch(props.delete_url, { method: 'DELETE' });  // Notify the backend
                    if (!response.ok) {
                        console.error("Error notifying backend of file deletion:", response.statusText);
                    }
                } catch (err) {
                    console.error("Error notifying backend of file deletion:", err);
                }
            }
        });

        return {
            file,
        };
    },

    methods: {
        async file_pick() {
            setTimeout(async () => {
                const m_file = this._.subTree.props.modelValue;

                if (!m_file) return;
                if (this.file_url) URL.revokeObjectURL(this.file_url);

                this.file_url = URL.createObjectURL(m_file);

                const m_return = {
                    name: m_file.name,
                    size: m_file.size,
                    type: m_file.type,
                    url: this.file_url,
                    last_modified: m_file.lastModified,
                };

                // Send the blob data to the backend endpoint
                const formData = new FormData();
                formData.append('file', m_file);

                try {
                    const response = await fetch(this.url, {
                        method: 'POST',
                        body: formData
                    });

                    if (response.ok) {
                        console.log("File sent to the backend successfully.");
                    } else {
                        console.error("Error sending the file to the backend:", response.statusText);
                    }
                } catch (err) {
                    console.error("Error sending the file to the backend:", err);
                }

                this.$emit("file_pick", m_return);
            }, 0);
        },
    },
  };