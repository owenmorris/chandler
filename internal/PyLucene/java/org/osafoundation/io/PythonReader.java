
package org.osafoundation.io;

import java.io.Reader;
import java.io.IOException;

/**
 * @author Andi Vajda
 */

public class PythonReader extends Reader {

    protected long pythonReader;

    public PythonReader(long pythonReader)
    {
        this.pythonReader = pythonReader;
    }

    public native void close()
        throws IOException;

    public native int read(char[] buf, int off, int len)
        throws IOException;
}
