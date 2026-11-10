import React, { useState } from 'react';
import { PRODUCT_IMAGE_FALLBACK, resolveImageSource } from '../services/catalogImages';

export default function CatalogImage({ src, alt, ...props }) {
  const resolved = resolveImageSource(src);
  const [failedSource, setFailedSource] = useState(null);
  return (
    <img
      loading="lazy"
      decoding="async"
      {...props}
      src={failedSource === resolved ? PRODUCT_IMAGE_FALLBACK : resolved}
      alt={alt}
      onError={() => setFailedSource(resolved)}
    />
  );
}
