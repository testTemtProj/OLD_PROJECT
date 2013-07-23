using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using MongoDB.Driver;
using System.Threading;

namespace AdvertiseShow
{
    class MongoConnectionPool
    {
        protected MongoConnectionPool() { }

        private sealed class SingletonCreator
        {
            private static readonly MongoConnectionPool instance = new MongoConnectionPool();
            public static MongoConnectionPool Instance { get { return instance; } }
        }

        public static int MaxConnections { get { return 5; } }

        static MongoConnectionPool()
        {
            for (int i = 0; i < MaxConnections; i++)
            {
                var connection = new Mongo();
                if (!connection.Connect())
                    return;
                pool_.Enqueue(connection);
            }
        }

        public static Mongo get()
        {
            if (!semaphore.WaitOne())
                return null;
            return pool_.Dequeue();
        }


        public static void back(Mongo connection)
        {
            if (connection == null) return;
            pool_.Enqueue(connection);
            semaphore.Release();
        }

        private static Queue<Mongo> pool_ = new Queue<Mongo>();
        private static Mutex mutex;
        private static Semaphore semaphore = new Semaphore(MaxConnections, MaxConnections);
    }
}
