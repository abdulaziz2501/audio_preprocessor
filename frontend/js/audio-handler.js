/**
 * Audio Handler - Backend API bilan ishlash
 * Fayl yuklash, processing va yuklab olish funksiyalari
 */

const AudioHandler = {
    // API base URL
    API_URL: 'http://localhost:8000/api/v1',
    
    // Hozirgi fayl ma'lumotlari
    currentFile: {
        id: null,
        name: null,
        size: null
    },
    
    /**
     * Fayl tanlanganda
     */
    async handleFileSelect(file) {
        console.log('📁 Fayl tanlandi:', file.name);
        
        // Fayl formatini tekshirish
        const allowedFormats = ['audio/mpeg', 'audio/wav', 'audio/x-m4a', 'audio/ogg', 'audio/flac'];
        if (!allowedFormats.includes(file.type) && !this.isAudioFile(file.name)) {
            UIController.showError('Noto\'g\'ri fayl formati. Faqat audio fayllar qo\'llab-quvvatlanadi.');
            return;
        }
        
        // Fayl hajmini tekshirish (100MB dan kichik bo'lishi kerak)
        const maxSize = 100 * 1024 * 1024; // 100MB
        if (file.size > maxSize) {
            UIController.showError('Fayl juda katta. Maksimal hajm: 100MB');
            return;
        }
        
        // Faylni yuklash
        await this.uploadFile(file);
    },
    
    /**
     * Fayl audio ekanligini tekshirish
     */
    isAudioFile(filename) {
        const audioExtensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac'];
        return audioExtensions.some(ext => filename.toLowerCase().endsWith(ext));
    },
    
    /**
     * Faylni serverga yuklash
     */
    async uploadFile(file) {
        UIController.showUploadProgress();
        UIController.updateProgress(0, 'Fayl yuklanmoqda...');
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            // XMLHttpRequest orqali yuklash (progress tracking uchun)
            const response = await this.uploadWithProgress(formData, (progress) => {
                UIController.updateProgress(progress, `Yuklanmoqda... ${progress}%`);
            });
            
            if (response.success) {
                // Fayl ma'lumotlarini saqlash
                this.currentFile.id = response.file_id;
                this.currentFile.name = response.filename;
                this.currentFile.size = (file.size / (1024 * 1024)).toFixed(2);
                
                console.log('✅ Fayl yuklandi:', response);
                
                // UI'ni yangilash
                UIController.showFileInfo(this.currentFile.name, this.currentFile.size);
                UIController.showProcessingOptions();
            } else {
                throw new Error(response.message || 'Fayl yuklashda xatolik');
            }
            
        } catch (error) {
            console.error('❌ Yuklash xatosi:', error);
            UIController.showError('Fayl yuklashda xatolik yuz berdi: ' + error.message);
        }
    },
    
    /**
     * Progress tracking bilan yuklash
     */
    uploadWithProgress(formData, onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            // Progress event
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    onProgress(percent);
                }
            });
            
            // Load event
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    resolve(response);
                } else {
                    reject(new Error(`Server xatosi: ${xhr.status}`));
                }
            });
            
            // Error event
            xhr.addEventListener('error', () => {
                reject(new Error('Tarmoq xatosi'));
            });
            
            // So'rovni yuborish
            xhr.open('POST', `${this.API_URL}/upload`);
            xhr.send(formData);
        });
    },
    
    /**
     * Audio'ni qayta ishlash
     */
    async processAudio() {
        if (!this.currentFile.id) {
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
        UIController.showProcessingStatus();
        
        try {
            // Agar faqat bitta operatsiya bo'lsa
            if (Object.keys(operations).length === 1) {
                await this.processSingleOperation(operations);
            } else {
                // Ko'p operatsiyalar uchun
                await this.processMultipleOperations(operations);
            }
            
        } catch (error) {
            console.error('❌ Processing xatosi:', error);
            UIController.showError('Qayta ishlashda xatolik: ' + error.message);
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
     * Bitta operatsiyani bajarish
     */
    async processSingleOperation(operations) {
        const formData = new FormData();
        formData.append('file_id', this.currentFile.id);
        
        // Noise Reduction
        if (operations.noise_reduction) {
            formData.append('noise_reduction_strength', operations.noise_reduction.strength);
            const response = await this.fetchAPI('/process/noise-reduction', formData);
            
            if (response) {
                UIController.showResults(response);
            }
        }
        
        // Silence Removal
        else if (operations.remove_silence) {
            formData.append('silence_threshold', operations.remove_silence.threshold);
            formData.append('min_silence_duration', operations.remove_silence.min_duration);
            const response = await this.fetchAPI('/process/remove-silence', formData);
            
            if (response) {
                UIController.showResults(response);
            }
        }
        
        // Segmentation
        else if (operations.segmentation) {
            formData.append('segment_duration', operations.segmentation.duration);
            formData.append('overlap', operations.segmentation.overlap);
            const response = await this.fetchAPI('/process/segmentation', formData);
            
            if (response && response.segments) {
                UIController.showResults(response.segments);
            }
        }
    },
    
    /**
     * Ko'p operatsiyalarni ketma-ket bajarish
     */
    async processMultipleOperations(operations) {
        const formData = new FormData();
        formData.append('file_id', this.currentFile.id);
        formData.append('operations', JSON.stringify(operations));
        
        const response = await this.fetchAPI('/process/complete', formData);
        
        if (response) {
            if (response.segments) {
                UIController.showResults(response.segments);
            } else {
                UIController.showResults(response);
            }
        }
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
    },
    
    /**
     * Barcha fayllarni zip qilib yuklab olish (agar segmentlar bo'lsa)
     */
    async downloadAllSegments(segments) {
        console.log('📦 Barcha segmentlar yuklab olinmoqda...');
        
        // Har bir segmentni alohida yuklab olish
        for (const segment of segments) {
            await this.downloadFile(segment.file_path);
            
            // Biroz kutish (too many requests oldini olish uchun)
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        console.log('✅ Barcha segmentlar yuklab olindi');
    }
};

// Global funksiya (HTML'dan chaqirish uchun)
async function processAudio() {
    await AudioHandler.processAudio();
}

console.log('✅ Audio Handler initialized');
