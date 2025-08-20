import React from 'react';
import { motion } from 'framer-motion';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex items-center p-4">
      <div className="bg-gray-200 rounded-lg p-3 flex items-center space-x-2">
        <span className="text-sm text-gray-500">Chatbot is typing</span>
        <motion.div
          className="flex space-x-1"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {[0, 1, 2].map((dot) => (
            <motion.div
              key={dot}
              className="w-2 h-2 bg-gray-400 rounded-full"
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.4, 1, 0.4],
              }}
              transition={{
                duration: 1.2,
                repeat: Infinity,
                delay: dot * 0.2,
              }}
            />
          ))}
        </motion.div>
      </div>
    </div>
  );
};
