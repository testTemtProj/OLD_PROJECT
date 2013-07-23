using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace AdvertiseShow
{
    class RandomEntity<EntityType>
    {
        public void Add(EntityType item, double weight)
        {
            items_.Add(new KeyValuePair<EntityType, double>(item, weight));
            totalWeight_ += weight;
        }

        public bool IsEmpty()
        {
            return items_.Count == 0;
        }

        public void Clear()
        {
            items_.Clear();
            totalWeight_ = 0;
        }

        /// <summary>
        /// Возвращает случайный элемент, с учётом их весов
        /// </summary>
        /// <returns></returns>
        public EntityType get()
        {
            double x = random.NextDouble() * totalWeight_;
            double c = 0;
            foreach (var pair in items_)
            {
                c += pair.Value;
                if (x <= c)
                    return pair.Key;
            }
            return default(EntityType);
        }

        private List<KeyValuePair<EntityType, double>> items_ = new List<KeyValuePair<EntityType, double>>();
        private double totalWeight_ = 0;
        private static Random random = new Random(DateTime.Now.Millisecond);
    }

        
    
}
