/**
 * Audio Handler - Backend API bilan ishlash
 * Fayl yuklash, processing va yuklab olish funksiyalari
 */

const AudioHandler = {
    // API base URL
    API_URL: 'http://localhost:8000/api/v1',
    
    // Hozirgi fayllar ro'yxati
    uploadedFiles: [],

    /**
     * Fayl tanlanganda (bitta yoki ko'p)
     */
    async handleFileSelect(files) {
        // Agar bitta fayl bo'lsa, uni array'ga o'tkazish
        if (!Array.isArray(files)) {
            files = [files];
        }

        console.log(`📁 ${files.length} ta fayl tanlandi`);

        // Har bir faylni tekshirish va yuklash
        const validFiles = [];
        const maxSize = 100 * 1024 * 1024; // 100MB

        for (const file of files) {
            // Format tekshirish
            if (!this.isAudioFile(file.name)) {
                console.warn(`⚠️ Noto'g'ri format: ${file.name}`);
                continue;
            }

            // Hajm tekshirish
            if (file.size > maxSize) {
                console.warn(`⚠️ Fayl juda katta: ${file.name}`);
                continue;
            }

            validFiles.push(file);
        }

        if (validFiles.length === 0) {
            UIController.showError('Hech qanday to\'g\'ri audio fayl topilmadi.');
            return;
        }

        // Barcha fayllarni yuklash
        await this.uploadMultipleFiles(validFiles);
    },

    /**
     * Fayl audio ekanligini tekshirish
     */
    isAudioFile(filename) {
        const audioExtensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac'];
        return audioExtensions.some(ext => filename.toLowerCase().endsWith(ext));
    },

    /**
     * Ko'p fayllarni yuklash
     */
    async uploadMultipleFiles(files) {
        UIController.showUploadProgress();
        UIController.clearFileList();

        this.uploadedFiles = [];
        let successCount = 0;

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const progress = Math.round(((i + 1) / files.length) * 100);

            UIController.updateProgress(
                progress,
                `Yuklanmoqda... ${i + 1}/${files.length}`
            );

            try {
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch(`${this.API_URL}/upload`, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();

                    this.uploadedFiles.push({
                        file_id: data.file_id,
                        filename: data.filename,
                        size: (file.size / (1024 * 1024)).toFixed(2),
                        status: 'success'
                    });

                    successCount++;

                    // UI'ga qo'shish
                    UIController.addFileToList({
                        filename: data.filename,
                        size: (file.size / (1024 * 1024)).toFixed(2),
                        status: 'success'
                    });

                    console.log(`✅ Yuklandi: ${file.name}`);
                } else {
                    throw new Error('Yuklashda xatolik');
                }

            } catch (error) {
                console.error(`❌ Xato ${file.name}:`, error);

                this.uploadedFiles.push({
                    filename: file.name,
                    size: (file.size / (1024 * 1024)).toFixed(2),
                    status: 'error'
                });

                UIController.addFileToList({
                    filename: file.name,
                    size: (file.size / (1024 * 1024)).toFixed(2),
                    status: 'error'
                });
            }
        }

        UIController.hideUploadProgress();
        UIController.showFileInfo(successCount);

        if (successCount > 0) {
            UIController.showProcessingOptions();
        }

        console.log(`✅ ${successCount}/${files.length} fayl yuklandi`);
    },

    /**
     * Audio'ni qayta ishlash (batch yoki single)
     */
    async processAudio() {
        if (this.uploadedFiles.length === 0) {
            UIController.showError('Iltimos, avval fayl yuklang');
            return;
        }

        // Tanlangan operatsiyalarni olish
        const operations = this.getSelectedOperations();

        if (Object.keys(operations).length === 0) {
            UIController.showError('Iltimos, kamida bitta operatsiyani tanlang');
            return;
        }

        console.log('🔧 Processing boshlandi:', operations);
        console.log(`📦 ${this.uploadedFiles.length} ta fayl qayta ishlanmoqda`);

        UIController.showProcessingStatus(
            `Processing ${this.uploadedFiles.length} Files...`,
            'Please wait, this may take a while'
        );

        try {
            // Batch processing
            await this.processBatch(operations);

        } catch (error) {
            console.error('❌ Processing xatosi:', error);
            UIController.showError('Qayta ishlashda xatolik: ' + error.message);
        }
    },

    /**
     * Batch processing - ko'p fayllarni bir vaqtda qayta ishlash
     */
    async processBatch(operations) {
        const formData = new FormData();

        // Faqat success fayllarni olish
        const successFiles = this.uploadedFiles.filter(f => f.status === 'success');
        const fileIds = successFiles.map(f => f.file_id);

        formData.append('file_ids', JSON.stringify(fileIds));
        formData.append('operations', JSON.stringify(operations));

        const response = await this.fetchAPI('/process/batch', formData);

        if (response && response.results) {
            // Natijalarni ko'rsatish
            UIController.showBatchResults(response.results, response);
        }
    },

    /**
     * Tanlangan operatsiyalarni olish
     */
    getSelectedOperations() {
        const operations = {};

        // Noise Reduction
        if (UIController.elements.noiseToggle.checked) {
            operations.noise_reduction = {
                strength: parseFloat(UIController.elements.noiseStrength.value)
            };
        }

        // Silence Removal
        if (UIController.elements.silenceToggle.checked) {
            operations.remove_silence = {
                threshold: parseInt(UIController.elements.silenceThreshold.value),
                min_duration: parseInt(UIController.elements.silenceDuration.value)
            };
        }

        // Segmentation
        if (UIController.elements.segmentToggle.checked) {
            operations.segmentation = {
                duration: parseInt(UIController.elements.segmentDuration.value),
                overlap: parseInt(UIController.elements.segmentOverlap.value)
            };
        }

        return operations;
    },

    /**
     * API ga so'rov yuborish
     */
    async fetchAPI(endpoint, formData) {
        try {
            const response = await fetch(`${this.API_URL}${endpoint}`, {
                method: 'POST',
                body: formData
            });

            // Agar response file bo'lsa
            if (response.headers.get('content-type')?.includes('audio')) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                return url;
            }

            // JSON response
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Server xatosi');
            }

            return data;

        } catch (error) {
            console.error('❌ API xatosi:', error);
            throw error;
        }
    },

    /**
     * Faylni yuklab olish
     */
    async downloadFile(filePath) {
        try {
            console.log('⬇️ Fayl yuklab olinmoqda:', filePath);

            // Agar blob URL bo'lsa
            if (filePath.startsWith('blob:')) {
                const a = document.createElement('a');
                a.href = filePath;
                a.download = 'processed_audio.wav';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                return;
            }

            // Server'dan yuklab olish
            const filename = filePath.split('/').pop();
            const response = await fetch(`${this.API_URL}/download/${filename}`);

            if (!response.ok) {
                throw new Error('Fayl topilmadi');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            URL.revokeObjectURL(url);

            console.log('✅ Fayl yuklab olindi');

        } catch (error) {
            console.error('❌ Yuklab olish xatosi:', error);
            UIController.showError('Faylni yuklab olishda xatolik: ' + error.message);
        }
    }
};

// Global funksiya (HTML'dan chaqirish uchun)
async function processAudio() {
    await AudioHandler.processAudio();
}

console.log('✅ Audio Handler initialized');