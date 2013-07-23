using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.IO;

namespace YottosCatalog.Filters {
    public abstract class CatalogFilterBase : Stream {
        protected Stream baseStream;
        protected YottosCatalogDataContext database;
        protected YottosCatalogUrlMappingsDataContext mappingDatabase;
        protected List<byte> responseBytes = new List<byte>(200000);

        private CatalogFilterBase() { }

        public CatalogFilterBase(Stream responseStream, YottosCatalogDataContext Database, YottosCatalogUrlMappingsDataContext MappingDatabase) {
            baseStream = responseStream;
            database = Database;
            mappingDatabase = MappingDatabase;
        }

        public sealed override bool CanRead { get { return baseStream.CanRead; } }
        public sealed override bool CanSeek { get { return baseStream.CanSeek; } }
        public sealed override bool CanWrite { get { return baseStream.CanWrite; } }

        public sealed override long Length { get { return baseStream.Length; } }

        public sealed override long Position {
            get { return baseStream.Position; }
            set { baseStream.Position = value; }
        }

        public sealed override int Read(byte[] buffer, int offset, int count) {
            return baseStream.Read(buffer, offset, count);
        }

        public sealed override long Seek(long offset, SeekOrigin origin) {
            return baseStream.Seek(offset, origin);
        }

        public sealed override void SetLength(long value) {
            baseStream.SetLength(value);
        }

        protected abstract void BeforeFlush();

        public sealed override void Flush() {
            BeforeFlush();
            baseStream.Flush();
        }

        public sealed override void Write(byte[] buffer, int offset, int count) {
            responseBytes.AddRange(buffer);
        }
    }
}
