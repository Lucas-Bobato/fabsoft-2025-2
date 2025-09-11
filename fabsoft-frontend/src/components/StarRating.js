"use client";
import { useState } from 'react';

// O `icon` pode ser 'star', 'whistle', etc. para reutilização
export default function StarRating({ initialValue = 0, onRatingChange, icon: IconComponent }) {
    const [rating, setRating] = useState(initialValue);
    const [hoverRating, setHoverRating] = useState(0);

    const handleMouseMove = (e, index) => {
        const { left, width } = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - left;
        const hoverValue = x < width / 2 ? index + 0.5 : index + 1;
        setHoverRating(hoverValue);
    };

    const handleMouseLeave = () => {
        setHoverRating(0);
    };

    const handleClick = (value) => {
        const newRating = value === rating ? 0 : value;
        setRating(newRating);
        onRatingChange(newRating);
    };
    
    return (
        <div className="flex justify-center" onMouseLeave={handleMouseLeave}>
            {[...Array(5)].map((_, index) => {
                const value = index + 1;
                const displayValue = hoverRating || rating;
                
                return (
                    <div
                        key={index}
                        className="relative cursor-pointer"
                        onMouseMove={(e) => handleMouseMove(e, index)}
                        onClick={() => handleClick(hoverRating)}
                    >
                        <IconComponent className="w-8 h-8 text-gray-600" />
                        <div
                            className="absolute top-0 left-0 h-full overflow-hidden"
                            style={{ width: displayValue >= value ? '100%' : (displayValue >= value - 0.5 ? '50%' : '0%') }}
                        >
                            <IconComponent className="w-8 h-8 text-yellow-400" />
                        </div>
                    </div>
                );
            })}
        </div>
    );
}