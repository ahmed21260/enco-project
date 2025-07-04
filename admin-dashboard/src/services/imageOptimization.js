import imageCompression from 'browser-image-compression';

// Configuration Cloudinary
const CLOUDINARY_CLOUD_NAME = 'enco-prestarail';
const CLOUDINARY_UPLOAD_PRESET = 'enco_photos';

// Configuration de compression
const COMPRESSION_OPTIONS = {
  maxSizeMB: 1,
  maxWidthOrHeight: 1920,
  useWebWorker: true,
  fileType: 'image/jpeg',
  quality: 0.8
};

// Configuration Cloudinary
const CLOUDINARY_OPTIONS = {
  cloud_name: CLOUDINARY_CLOUD_NAME,
  upload_preset: CLOUDINARY_UPLOAD_PRESET,
  folder: 'enco_photos',
  transformation: [
    { width: 1920, height: 1080, crop: 'limit' },
    { quality: 'auto', fetch_format: 'auto' }
  ]
};

/**
 * Compresse une image avant upload
 */
export const compressImage = async (file) => {
  try {
    console.log('🔄 Compression de l\'image...', file.name);
    
    const compressedFile = await imageCompression(file, COMPRESSION_OPTIONS);
    
    console.log('✅ Image compressée:', {
      original: `${(file.size / 1024 / 1024).toFixed(2)} MB`,
      compressed: `${(compressedFile.size / 1024 / 1024).toFixed(2)} MB`,
      reduction: `${((file.size - compressedFile.size) / file.size * 100).toFixed(1)}%`
    });
    
    return compressedFile;
  } catch (error) {
    console.error('❌ Erreur compression:', error);
    return file; // Retourne l'original si erreur
  }
};

/**
 * Upload vers Cloudinary avec optimisation automatique
 */
export const uploadToCloudinary = async (file, operatorId, type = 'photo') => {
  try {
    console.log('☁️ Upload vers Cloudinary...', file.name);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('upload_preset', CLOUDINARY_UPLOAD_PRESET);
    formData.append('cloud_name', CLOUDINARY_CLOUD_NAME);
    formData.append('folder', `enco_photos/${operatorId}/${type}`);
    formData.append('transformation', 'w_1920,h_1080,c_limit,q_auto,f_auto');
    
    const response = await fetch(`https://api.cloudinary.com/v1_1/${CLOUDINARY_CLOUD_NAME}/image/upload`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
    
    const result = await response.json();
    
    console.log('✅ Upload Cloudinary réussi:', {
      url: result.secure_url,
      size: result.bytes,
      format: result.format
    });
    
    return {
      url: result.secure_url,
      publicId: result.public_id,
      size: result.bytes,
      format: result.format,
      width: result.width,
      height: result.height
    };
  } catch (error) {
    console.error('❌ Erreur upload Cloudinary:', error);
    throw error;
  }
};

/**
 * Optimise et upload une image complète
 */
export const optimizeAndUploadImage = async (file, operatorId, type = 'photo') => {
  try {
    // 1. Compression
    const compressedFile = await compressImage(file);
    
    // 2. Upload vers Cloudinary
    const uploadResult = await uploadToCloudinary(compressedFile, operatorId, type);
    
    return uploadResult;
  } catch (error) {
    console.error('❌ Erreur optimisation/upload:', error);
    throw error;
  }
};

/**
 * Batch upload pour plusieurs images
 */
export const batchUploadImages = async (files, operatorId, type = 'photo') => {
  const results = [];
  const batchSize = 3; // Upload 3 images à la fois
  
  for (let i = 0; i < files.length; i += batchSize) {
    const batch = files.slice(i, i + batchSize);
    
    console.log(`📦 Upload batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(files.length / batchSize)}`);
    
    const batchPromises = batch.map(file => 
      optimizeAndUploadImage(file, operatorId, type)
    );
    
    const batchResults = await Promise.allSettled(batchPromises);
    
    batchResults.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        results.push(result.value);
      } else {
        console.error(`❌ Erreur upload image ${i + index}:`, result.reason);
      }
    });
    
    // Pause entre les batches pour éviter la surcharge
    if (i + batchSize < files.length) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  
  return results;
};

/**
 * Génère une URL Cloudinary optimisée
 */
export const getOptimizedImageUrl = (publicId, options = {}) => {
  const defaultOptions = {
    width: 800,
    height: 600,
    crop: 'fill',
    quality: 'auto',
    format: 'auto'
  };
  
  const finalOptions = { ...defaultOptions, ...options };
  
  const transformations = [
    `w_${finalOptions.width}`,
    `h_${finalOptions.height}`,
    `c_${finalOptions.crop}`,
    `q_${finalOptions.quality}`,
    `f_${finalOptions.format}`
  ].join(',');
  
  return `https://res.cloudinary.com/${CLOUDINARY_CLOUD_NAME}/image/upload/${transformations}/${publicId}`;
};

/**
 * Supprime une image de Cloudinary
 */
export const deleteFromCloudinary = async (publicId) => {
  try {
    const response = await fetch(`/api/cloudinary/delete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ publicId })
    });
    
    if (!response.ok) {
      throw new Error('Erreur suppression image');
    }
    
    console.log('✅ Image supprimée de Cloudinary:', publicId);
    return true;
  } catch (error) {
    console.error('❌ Erreur suppression Cloudinary:', error);
    return false;
  }
}; 